# belong/repositories/lonely_forecast_repo.py

from typing import List, Dict, Any
from sqlalchemy import func

from belong.extensions import db
from belong.models.region import Region
from belong.models.elderly_history import ElderlyHistory  # ✅ 변경: ELDERLY_HISTORY 사용
from belong.models.prediction_result import PredictionResult  # PREDICTION_RESULT


class LonelyForecastRepository:
    """
    고독사 모달(한 구 상세)을 위해
    - ELDERLY_HISTORY(실측) - seed_data.py로 채워진 테이블
    - PREDICTION_RESULT(예측)
    를 조회하는 전용 레포지토리.
    """

    def get_history(self, region_name: str, max_year: int | None = None) -> List[Dict[str, Any]]:
        """
        ELDERLY_HISTORY에서 해당 구의 '실측' 고독사 데이터를 연도별로 조회.

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
            return []

        # 2) ELDERLY_HISTORY에서 연도별 합계 조회 (is_forecast='N'인 실측 데이터만)
        q = (
            db.session.query(
                ElderlyHistory.year.label("year"),
                func.sum(ElderlyHistory.elderly_population).label("value"),
            )
            .filter(ElderlyHistory.region_id == region.id)
            .filter(ElderlyHistory.is_forecast == 'N')  # 실측 데이터만
        )

        if max_year is not None:
            q = q.filter(ElderlyHistory.year <= max_year)

        rows = (
            q.group_by(ElderlyHistory.year)
            .order_by(ElderlyHistory.year.asc())
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
