import pandas as pd
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from belong.extensions import db
# ⚠️ 실제 ElderlyStats 모델 경로에 맞게 수정 필요
# 예: from belong.models.elderly_stats import ElderlyStats
from belong.models.feature_stats import ElderlyStats


# ---- 분석에 사용할 컬럼 정의 (ORM 속성명 기준) ----
FEATURE_COLUMNS: List[str] = [
    "single_household_ratio",  # 1인가구 비율
    "aging_index",             # 고령화 지수
    "cpi_index",               # 소비자 물가
    "age_65_over",             # 65세 이상 노인 수
    "single_house_total",      # 1인 가구 수
]

TARGET_COLUMN: str = "elderly_population"  # 타깃 컬럼 (현재는 노인 인구 수)


FEATURE_DESC: Dict[str, str] = {
    "single_household_ratio": "1인가구 비율",
    "aging_index": "고령화 지수",
    "cpi_index": "소비자 물가",
    "age_65_over": "65세 이상 노인 수",
    "single_house_total": "1인 가구 수",
}


class CorrelationService:
    """
    ELDERLY_STATS 테이블 기반 상관관계 분석 서비스.

    - 기존: ml/dataset/merged_dataset.csv 파일을 직접 읽어서 상관계수 계산
    - 변경: Oracle DB의 ELDERLY_STATS 테이블에서 데이터를 읽어와 계산

    기본 타깃은 elderly_population(노인 인구 수)이고,
    FEATURE_COLUMNS에 정의된 5개 피처와의 피어슨 상관계수를 계산함.
    """

    def __init__(self, session: Optional[Session] = None):
        # 세션 주입 가능하게 만들어두면 나중에 테스트/DI에 유리함
        self.session: Session = session or db.session

    # ------------------------------------------------------------------
    # 내부: DB → pandas.DataFrame 로딩
    # ------------------------------------------------------------------
    def _load_dataframe(
        self,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        region_ids: Optional[List[int]] = None,
    ) -> Optional[pd.DataFrame]:
        """
        ELDERLY_STATS에서 필요한 행들을 조회해서 pandas.DataFrame으로 변환.

        year_from/year_to, region_ids 로 간단한 필터링을 할 수 있게 해놨지만,
        지금 API에서는 파라미터 없이 전체 기간을 대상으로 사용해도 됨.
        """
        query = self.session.query(ElderlyStats)

        if year_from is not None:
            query = query.filter(ElderlyStats.year >= year_from)
        if year_to is not None:
            query = query.filter(ElderlyStats.year <= year_to)
        if region_ids:
            query = query.filter(ElderlyStats.region_id.in_(region_ids))

        rows: List[ElderlyStats] = query.all()
        if not rows:
            return None

        records: List[Dict[str, Any]] = []
        for r in rows:
            # ORM 속성명 기준으로 dict 구성
            record: Dict[str, Any] = {
                TARGET_COLUMN: getattr(r, TARGET_COLUMN, None),
            }
            for col in FEATURE_COLUMNS:
                record[col] = getattr(r, col, None)
            records.append(record)

        df = pd.DataFrame(records)
        if df.empty:
            return None
        return df

    # ------------------------------------------------------------------
    # 외부: 상관계수 계산 메인 메서드
    # ------------------------------------------------------------------
    def compute(
        self,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        region_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        상관계수 계산 로직 (DB 기반):

        1. ELDERLY_STATS에서 필요한 행들을 조회해서 DataFrame으로 로드
        2. 타깃 컬럼 + 피처 컬럼들을 숫자형(float)으로 강제 변환
        3. NaN 포함된 행 제거
        4. 피어슨 상관계수 계산
        5. JSON 형태로 반환

        반환 구조:
        {
          "correlations": [
            {"feature": "single_household_ratio", "corr": 0.82},
            ...
          ],
          "feature_desc": { ... }
        }
        """
        df = self._load_dataframe(
            year_from=year_from,
            year_to=year_to,
            region_ids=region_ids,
        )

        if df is None:
            return {
                "correlations": [],
                "feature_desc": FEATURE_DESC,
            }

        # 원본 훼손 방지
        df = df.copy()

        numeric_columns: List[str] = [TARGET_COLUMN] + FEATURE_COLUMNS

        # ---- 숫자 변환 단계 ----
        for col in numeric_columns:
            if col not in df.columns:
                # 모델/DB 정의가 바뀌었는데 코드가 안 맞는 경우 대비
                continue
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # ---- 결측치 제거 ----
        before_count: int = len(df)
        df = df.dropna(subset=[c for c in numeric_columns if c in df.columns])
        after_count: int = len(df)

        dropped_rows: int = before_count - after_count
        if dropped_rows > 0:
            # 로그로 남겨두면 데이터 품질 체크에 도움됨
            print(f"[CorrelationService] {dropped_rows} rows dropped due to NaN.")

        # 타깃 컬럼 없으면 빈 결과
        if TARGET_COLUMN not in df.columns:
            return {
                "correlations": [],
                "feature_desc": FEATURE_DESC,
            }

        target_series = df[TARGET_COLUMN]

        # ---- 상관계수 계산 ----
        results: Dict[str, float] = {}
        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                continue

            # 피어슨 상관계수
            corr_value = df[col].corr(target_series)
            if pd.isna(corr_value):
                continue

            results[col] = round(float(corr_value), 4)

        # ---- 결과 JSON 변환 ----
        correlations: List[Dict[str, Any]] = [
            {"feature": feature, "corr": value}
            for feature, value in results.items()
        ]

        # 절댓값 기준으로 내림차순 정렬하면 더 보기 좋음
        correlations.sort(key=lambda x: abs(x["corr"]), reverse=True)

        return {
            "correlations": correlations,
            "feature_desc": FEATURE_DESC,
        }
