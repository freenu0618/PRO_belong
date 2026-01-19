# inference_server/mcp/tools/prediction_tool.py
"""PredictionTool - 고독사 예측 실행 도구"""

import logging
import asyncio
from typing import Dict, Any

from .base import BaseTool

logger = logging.getLogger(__name__)


class PredictionTool(BaseTool):
    """
    특정 지역과 연도에 대한 고독사 발생 건수 예측

    기능:
    - ML 모델 기반 예측 실행
    - 과거 데이터 기반 추세 분석
    - belong/services/prediction_service.py 재사용
    """

    def get_schema(self) -> Dict[str, Any]:
        """
        Tool Schema (OpenAI Function Calling 표준 형식)

        Returns:
            {
                "type": "function",
                "function": {
                    "name": "prediction",
                    "description": "...",
                    "parameters": {...}
                }
            }
        """
        return {
            "type": "function",
            "function": {
                "name": "prediction",
                "description": (
                    "특정 지역과 연도에 대한 고독사 발생 건수를 예측합니다. "
                    "ML 모델 또는 통계 기반 분석을 통해 예측값을 계산하고, "
                    "과거 데이터와 함께 추세를 제공합니다."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "예측할 지역명 (예: '강남구', '서초구')",
                            "minLength": 2
                        },
                        "year": {
                            "type": "integer",
                            "description": "예측할 연도 (예: 2025, 2026)",
                            "minimum": 2024,
                            "maximum": 2035
                        }
                    },
                    "required": ["region", "year"]
                }
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        예측 실행 (비동기)

        Args:
            arguments: {
                "region": "강남구" (필수),
                "year": 2025 (필수)
            }

        Returns:
            {
                "success": True,
                "region": "강남구",
                "year": 2025,
                "prediction": 178.3,
                "source": "ml_model",
                "history": [
                    {"year": 2023, "value": 165},
                    {"year": 2024, "value": 172}
                ],
                "trend": "increasing"
            }
            또는
            {
                "success": False,
                "error": "에러 메시지"
            }
        """
        # 인자 추출
        region = arguments.get("region", "")
        year = arguments.get("year")

        if not region or not year:
            return {
                "success": False,
                "error": "Both 'region' and 'year' parameters are required"
            }

        logger.info(f"[PredictionTool] Predicting: region={region}, year={year}")

        try:
            # 예측 실행 (동기 함수를 비동기로 실행)
            result = await asyncio.to_thread(
                self._execute_prediction, region, year
            )

            logger.info(f"[PredictionTool] Prediction complete: {result['prediction']:.1f}")

            return {
                "success": True,
                **result
            }

        except Exception as e:
            logger.error(f"[PredictionTool] Prediction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "region": region,
                "year": year
            }

    def _execute_prediction(self, region: str, year: int) -> Dict[str, Any]:
        """
        실제 예측 로직 (동기)

        Args:
            region: 지역명
            year: 연도

        Returns:
            예측 결과 딕셔너리
        """
        # belong/services/prediction_service.py 재사용 시도
        try:
            from belong.services.prediction_service import predict_region_year

            # 예측 실행
            prediction_value = predict_region_year(region, year)

            # 과거 데이터 조회 (추세 분석용)
            history = self._get_historical_trend(region)

            # 추세 분석
            trend = self._analyze_trend(history)

            return {
                "region": region,
                "year": year,
                "prediction": round(prediction_value, 1),
                "source": "ml_model",
                "history": history,
                "trend": trend
            }

        except ImportError:
            # prediction_service가 없는 경우 간단한 룰 기반 예측
            logger.warning("[PredictionTool] prediction_service not found, using fallback")
            return self._fallback_prediction(region, year)

    def _get_historical_trend(self, region: str) -> list:
        """
        과거 데이터 조회 (추세 분석용)

        Args:
            region: 지역명

        Returns:
            [{"year": 2023, "value": 165}, ...]
        """
        try:
            import os
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                return []

            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                from belong.services.ai.db_rag import DBRagService
                service = DBRagService(session)

                # 과거 데이터 조회
                historical_data = service.get_historical_data([region])

                # 포맷 변환
                history = [
                    {"year": item["year"], "value": item["value"]}
                    for item in historical_data
                    if item["region"] == region
                ]

                return sorted(history, key=lambda x: x["year"])

            finally:
                session.close()

        except Exception as e:
            logger.warning(f"[PredictionTool] Failed to get history: {e}")
            return []

    def _analyze_trend(self, history: list) -> str:
        """
        추세 분석

        Args:
            history: [{"year": 2023, "value": 165}, ...]

        Returns:
            "increasing", "decreasing", "stable", "unknown"
        """
        if len(history) < 2:
            return "unknown"

        # 최근 3년 추세 분석
        recent = history[-3:]
        values = [item["value"] for item in recent]

        # 간단한 선형 추세
        if all(values[i] < values[i+1] for i in range(len(values)-1)):
            return "increasing"
        elif all(values[i] > values[i+1] for i in range(len(values)-1)):
            return "decreasing"
        else:
            # 평균 변화율 계산
            avg_change = (values[-1] - values[0]) / len(values)
            if avg_change > 5:
                return "increasing"
            elif avg_change < -5:
                return "decreasing"
            else:
                return "stable"

    def _fallback_prediction(self, region: str, year: int) -> Dict[str, Any]:
        """
        Fallback 예측 (prediction_service가 없을 때)

        Args:
            region: 지역명
            year: 연도

        Returns:
            예측 결과 딕셔너리
        """
        # 간단한 룰 기반 예측
        # TODO: 실제 환경에서는 항상 prediction_service 사용 권장

        # 지역별 기본값 (예시)
        base_values = {
            "강남구": 120,
            "서초구": 150,
            "송파구": 170,
            # ... 다른 지역 추가 가능
        }

        base_value = base_values.get(region, 100)

        # 연도별 증가율 (예: 5% per year)
        growth_rate = 1.05
        years_from_2024 = year - 2024
        predicted_value = base_value * (growth_rate ** years_from_2024)

        return {
            "region": region,
            "year": year,
            "prediction": round(predicted_value, 1),
            "source": "rule_based",
            "history": [],
            "trend": "increasing"
        }
