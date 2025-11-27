# belong/services/lonely_forecast_service.py

from typing import Dict, Any, List

from sqlalchemy import func

from belong.extensions import db, logger
from belong.models.region import Region
from belong.models.feature_stats import ElderlyStats   # ELDERLY_STATS (target_value = 고독사 실측)
from belong.models.prediction_result import PredictionResult  # PREDICTION_RESULT (prediction_value = 고독사 예측)

# 고독사 실측이 끝나는 마지막 연도
ACTUAL_LAST_YEAR = 2023
# 지금 DB에 저장된 source 값 (rule_based)
LONELY_SOURCE = "rule_based"


class LonelyForecastService:
    """
    고독사 구별 실측/예측 시계열 조회 서비스.

    - history  : ELDERLY_STATS.target_value (year <= ACTUAL_LAST_YEAR)
    - forecast : PREDICTION_RESULT.prediction_value
                 (year > ACTUAL_LAST_YEAR, source = LONELY_SOURCE)
    """

    def forecast_region(self, region: str) -> Dict[str, Any]:
        """
        특정 구(region)에 대한 고독사 실측/예측 시계열을 반환.

        반환 형식:
        {
            "region": "강남구",
            "history": [
                {"year": 2017, "value": 10},
                ...
            ],
            "forecast": [
                {"year": 2025, "value": 14279},
                ...
            ],
            "message": "ELDERLY_STATS + PREDICTION_RESULT 기반 고독사 실측/예측 데이터입니다.",
        }
        """
        logger.info(f"[LonelyForecast] 요청 region={region}")

        # --------------------------------------------------
        # 1) 실측: ELDERLY_STATS.target_value (연도 <= 2023)
        # --------------------------------------------------
        actual_rows = (
            db.session.query(
                ElderlyStats.year.label("year"),
                func.sum(ElderlyStats.target_value).label("value"),
            )
            .join(Region, ElderlyStats.region_id == Region.id)
            .filter(
                Region.name == region,
                ElderlyStats.year <= ACTUAL_LAST_YEAR,
            )
            .group_by(ElderlyStats.year)
            .order_by(ElderlyStats.year)
            .all()
        )

        history: List[Dict[str, int]] = [
            {"year": int(r.year), "value": int(r.value or 0)}
            for r in actual_rows
        ]

        # --------------------------------------------------
        # 2) 예측: PREDICTION_RESULT.prediction_value
        #          (연도 > 2023, source = 'rule_based')
        # --------------------------------------------------
        forecast_rows = (
            db.session.query(
                PredictionResult.year.label("year"),
                func.sum(PredictionResult.prediction_value).label("value"),
            )
            .filter(
                PredictionResult.region_name == region,
                PredictionResult.source == LONELY_SOURCE,
                PredictionResult.year > ACTUAL_LAST_YEAR,
            )
            .group_by(PredictionResult.year)
            .order_by(PredictionResult.year)
            .all()
        )

        forecast: List[Dict[str, int]] = [
            {"year": int(r.year), "value": int(r.value or 0)}
            for r in forecast_rows
        ]

        # --------------------------------------------------
        # 3) 데이터가 하나도 없을 때
        # --------------------------------------------------
        if not history and not forecast:
            logger.warning(f"[LonelyForecast] 데이터 없음 region={region}")
            return {
                "region": region,
                "history": [],
                "forecast": [],
                "message": "해당 구의 고독사 실측/예측 데이터를 찾을 수 없습니다.",
            }

        return {
            "region": region,
            "history": history,
            "forecast": forecast,
            "message": "ELDERLY_STATS + PREDICTION_RESULT 기반 고독사 실측/예측 데이터입니다.",
        }
