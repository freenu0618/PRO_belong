from typing import List, Dict
from sqlalchemy import func

from belong.extensions import db
from belong.models.feature_stats import ElderlyStats  # target_value 컬럼 포함
from belong.models.prediction_result import PredictionResult
from belong.models.region import Region


ACTUAL_LAST_YEAR = 2023  # 실측 마지막 연도


class LonelyStatsRepository:
    """
    고독사(타깃: target_value) 추세/Top5/구별값 조회용 Repo.
    - 실측(ELDERLY_STATS.target_value)
    - 예측(PREDICTION_RESULT.prediction_value)
    를 합쳐서 사용.
    """

    def _query_actual_total(self, start_year: int, end_year: int):
        return (
            db.session.query(
                ElderlyStats.year.label("year"),
                func.sum(ElderlyStats.target_value).label("value"),
            )
            .join(Region, ElderlyStats.region_id == Region.id)
            .filter(ElderlyStats.year.between(start_year, end_year))
            .group_by(ElderlyStats.year)
            .all()
        )

    def _query_forecast_total(self, start_year: int, end_year: int):
        return (
            db.session.query(
                PredictionResult.year.label("year"),
                func.sum(PredictionResult.prediction_value).label("value"),
            )
            .filter(PredictionResult.year.between(start_year, end_year))
            .group_by(PredictionResult.year)
            .all()
        )

    def get_total_trend(self, start_year: int, end_year: int) -> List[Dict]:
        """
        연도별(전체 서울) 고독사 인원 추세.
        실측(<=2023) + 예측(>2023) 합쳐서 반환.
        """
        items: List[Dict] = []

        # 실측 구간
        actual_end = min(end_year, ACTUAL_LAST_YEAR)
        if start_year <= actual_end:
            for r in self._query_actual_total(start_year, actual_end):
                items.append(
                    {
                        "year": int(r.year),
                        "value": int(r.value or 0),
                        "is_forecast": False,
                    }
                )

        # 예측 구간
        forecast_start = max(start_year, ACTUAL_LAST_YEAR + 1)
        if forecast_start <= end_year:
            for r in self._query_forecast_total(forecast_start, end_year):
                items.append(
                    {
                        "year": int(r.year),
                        "value": int(r.value or 0),
                        "is_forecast": True,
                    }
                )

        # 연도 기준 정렬
        items.sort(key=lambda x: x["year"])
        return items

    # ---- Top5 계산용: base_year / target_year 값 ----
    def _get_region_values_for_year(self, year: int) -> List[Dict]:
        # 연도에 따라 실측 or 예측 테이블 선택
        if year <= ACTUAL_LAST_YEAR:
            q = (
                db.session.query(
                    Region.id.label("region_id"),
                    Region.name.label("region"),
                    ElderlyStats.year.label("year"),
                    ElderlyStats.target_value.label("value"),
                )
                .join(ElderlyStats, ElderlyStats.region_id == Region.id)
                .filter(ElderlyStats.year == year)
            )
        else:
            q = (
                db.session.query(
                    Region.id.label("region_id"),
                    Region.name.label("region"),
                    PredictionResult.year.label("year"),
                    PredictionResult.prediction_value.label("value"),
                )
                .join(
                    Region,
                    Region.name == PredictionResult.region_name,
                )
                .filter(PredictionResult.year == year)
            )

        rows = q.all()
        return [
            {
                "region_id": int(r.region_id),
                "region": str(r.region).strip(),
                "year": int(r.year),
                "value": int(r.value or 0),
            }
            for r in rows
        ]

    def get_region_values_for_years(self, base_year: int, target_year: int) -> List[Dict]:
        """
        base_year / target_year 한 번에 조회해서 merge하여 반환.
        """
        base_rows = self._get_region_values_for_year(base_year)
        target_rows = self._get_region_values_for_year(target_year)

        data = {}

        for r in base_rows:
            data[r["region"]] = {
                "region_id": r["region_id"],
                "region": r["region"],
                "base_year": base_year,
                "base_value": r["value"],
                "target_year": target_year,
                "target_value": None,
            }

        for r in target_rows:
            key = r["region"]
            if key not in data:
                data[key] = {
                    "region_id": r["region_id"],
                    "region": r["region"],
                    "base_year": base_year,
                    "base_value": None,
                    "target_year": target_year,
                    "target_value": r["value"],
                }
            else:
                data[key]["target_value"] = r["value"]

        return list(data.values())
