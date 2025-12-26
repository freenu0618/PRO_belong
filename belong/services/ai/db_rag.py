"""
DB RAG 서비스 - PostgreSQL 데이터를 RAG 컨텍스트로 제공
질문에서 지역명/연도를 추출하여 관련 데이터를 조회
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 서울 25개 구 목록
SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]

class DBRagService:
    """PostgreSQL 데이터를 RAG 컨텍스트로 변환하는 서비스"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
    
    def extract_entities(self, question: str) -> Dict:
        """
        질문에서 지역명과 연도 추출
        
        Args:
            question: 사용자 질문
            
        Returns:
            {"regions": ["강남구", ...], "years": [2024, 2025, ...]}
        """
        entities = {"regions": [], "years": []}
        
        # 지역명 추출
        for district in SEOUL_DISTRICTS:
            if district in question:
                entities["regions"].append(district)
        
        # 연도 추출 (2020-2030)
        years = re.findall(r'20[2-3][0-9]', question)
        entities["years"] = [int(y) for y in set(years)]
        
        return entities
    
    def get_prediction_data(self, regions: List[str] = None, years: List[int] = None) -> List[Dict]:
        """
        예측 데이터 조회
        
        Args:
            regions: 조회할 지역 목록 (None이면 전체)
            years: 조회할 연도 목록 (None이면 최근 5년)
        """
        if self.db_session is None:
            return []
        
        try:
            from belong.models.prediction_result import PredictionResult
            
            query = self.db_session.query(PredictionResult)
            
            if regions:
                query = query.filter(PredictionResult.region_name.in_(regions))
            
            if years:
                query = query.filter(PredictionResult.year.in_(years))
            else:
                # 기본: 2024-2028
                query = query.filter(PredictionResult.year.in_([2024, 2025, 2026, 2027, 2028]))
            
            results = query.order_by(PredictionResult.region_name, PredictionResult.year).all()
            
            return [
                {
                    "region": r.region_name,
                    "year": r.year,
                    "prediction": round(r.prediction_value, 1),
                    "source": r.source
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"DB query failed: {e}")
            return []
    
    def get_historical_data(self, regions: List[str] = None) -> List[Dict]:
        """과거 데이터 조회 (ElderlyHistory)"""
        if self.db_session is None:
            return []
        
        try:
            from belong.models.elderly_history import ElderlyHistory
            
            query = self.db_session.query(ElderlyHistory)
            
            if regions:
                query = query.filter(ElderlyHistory.region_name.in_(regions))
            
            # 최근 5년 데이터
            query = query.filter(ElderlyHistory.year >= 2019)
            results = query.order_by(ElderlyHistory.region_name, ElderlyHistory.year).all()
            
            return [
                {
                    "region": r.region_name,
                    "year": r.year,
                    "value": r.death_count if hasattr(r, 'death_count') else r.value
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Historical data query failed: {e}")
            return []
    
    def build_context(self, question: str) -> str:
        """
        질문에 맞는 DB 컨텍스트 생성
        
        Args:
            question: 사용자 질문
            
        Returns:
            DB 데이터가 포함된 컨텍스트 문자열
        """
        entities = self.extract_entities(question)
        regions = entities["regions"]
        years = entities["years"]
        
        # 특정 지역이 없으면 위험도 상위 5개 구 제공
        if not regions:
            regions = None  # 전체 조회
        
        # 예측 데이터 가져오기
        predictions = self.get_prediction_data(regions, years if years else None)
        
        if not predictions:
            return ""
        
        # 컨텍스트 구성
        context_parts = ["📊 **데이터베이스 정보 (실시간)**\n"]
        
        # 지역별로 그룹화
        region_data = {}
        for p in predictions:
            if p["region"] not in region_data:
                region_data[p["region"]] = []
            region_data[p["region"]].append(p)
        
        for region, data in region_data.items():
            context_parts.append(f"\n**{region}**:")
            for d in data:
                context_parts.append(f"  - {d['year']}년 예측: {d['prediction']}건")
        
        # 요약 통계 추가
        if len(predictions) > 1:
            total = sum(p["prediction"] for p in predictions)
            avg = total / len(predictions)
            max_pred = max(predictions, key=lambda x: x["prediction"])
            min_pred = min(predictions, key=lambda x: x["prediction"])
            
            context_parts.append(f"\n**요약 통계**:")
            context_parts.append(f"  - 총 예측 건수: {total:.0f}건")
            context_parts.append(f"  - 평균: {avg:.1f}건")
            context_parts.append(f"  - 최고 위험 지역: {max_pred['region']} ({max_pred['year']}년 {max_pred['prediction']}건)")
            context_parts.append(f"  - 최저 위험 지역: {min_pred['region']} ({min_pred['year']}년 {min_pred['prediction']}건)")
        
        return "\n".join(context_parts)


# 전역 인스턴스 (Flask 앱 컨텍스트에서 초기화)
db_rag_service = None

def init_db_rag(db_session):
    """Flask 앱 컨텍스트에서 DB RAG 서비스 초기화"""
    global db_rag_service
    db_rag_service = DBRagService(db_session)
    return db_rag_service

def get_db_context(question: str, db_session=None) -> str:
    """
    질문에 대한 DB 컨텍스트 반환 (외부 호출용)
    
    Args:
        question: 사용자 질문
        db_session: SQLAlchemy 세션 (None이면 전역 서비스 사용)
    """
    if db_session:
        service = DBRagService(db_session)
        return service.build_context(question)
    elif db_rag_service:
        return db_rag_service.build_context(question)
    else:
        return ""
