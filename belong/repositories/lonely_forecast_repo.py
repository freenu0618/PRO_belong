# belong/repositories/lonely_forecast_repo.py

from typing import List, Dict, Any
from sqlalchemy import func

from belong.extensions import db
from belong.models.region import Region
from belong.models.feature_stats import ElderlyStats  # ELDERLY_STATS
from belong.models.prediction_result import PredictionResult  # PREDICTION_RESULT


class LonelyForecastRepository:
    """
    고독사 모달(한 구 상세)을 위해
    - ELDERLY_STATS(실측),
    - PREDICTION_RESULT(예측)
    를 조회하는 전용 레포지토리.

    여기서는 'DB에서 꺼내서 리스트로 돌려주는 역할'만 한다.
    region, message, is_forecast 같은 가공은 Service가 맡는다.
    """

    def get_history(self, region_name: str, max_year: int | None = None) -> List[Dict[str, Any]]:
        """
        ELDERLY_STATS에서 해당 구의 '실측' 고독사 데이터를 연도별로 조회.

        반환 예:
        [
          {"year": 2017, "value": 10},
          {"year": 2018, "value": 12},
          ...
        ]
        """
        # 1) 구 ID 찾기
        region = (
            db.session.query(Region)
            .filter(Region.name == region_name)
            .first()
        )
        if region is None:
            # Repo는 그냥 빈 리스트만 주고, "없는 구" 메시지는 Service가 처리
            return []

        # 2) ELDERLY_STATS에서 연도별 합계 조회
        q = (
            db.session.query(
                ElderlyStats.year.label("year"),
                func.sum(ElderlyStats.target_value).label("value"),
            )
            .filter(ElderlyStats.region_id == region.id)
        )

        if max_year is not None:
            q = q.filter(ElderlyStats.year <= max_year)

        rows = (
            q.group_by(ElderlyStats.year)
            .order_by(ElderlyStats.year.asc())
            .all()
        )

        return [
            {
                "year": int(row.year),
                "value": int(row.value or 0),
            }
            for row in rows
        ]

    def get_forecast(
        self,
        region_name: str,
        min_year: int | None = None,
        source: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        PREDICTION_RESULT에서 해당 구의 '예측' 고독사 데이터를 연도별로 조회.

        반환 예:
        [
          {"year": 2024, "value": 20, "source": "model"},
          {"year": 2025, "value": 22, "source": "rule_based"},
          ...
        ]
        """
        q = (
            db.session.query(
                PredictionResult.year.label("year"),
                func.sum(PredictionResult.prediction_value).label("value"),
                func.max(PredictionResult.source).label("source"),
            )
            .filter(PredictionResult.region_name == region_name)
        )

        if min_year is not None:
            q = q.filter(PredictionResult.year >= min_year)

        if source is not None:
            q = q.filter(PredictionResult.source == source)

        rows = (
            q.group_by(PredictionResult.year)
            .order_by(PredictionResult.year.asc())
            .all()
        )

        return [
            {
                "year": int(row.year),
                "value": int(row.value or 0),
                "source": row.source,
            }
            for row in rows
        ]
