# belong/services/lonely_forecast_service.py

from __future__ import annotations

from typing import List, Dict, Any
from sqlalchemy import func

from belong.extensions import db, logger
from belong.models.region import Region
from belong.models.feature_stats import ElderlyStats  # ELDERLY_STATS (target_value = 실측)
from belong.models.prediction_result import (
    PredictionResult,
)  # PREDICTION_RESULT (prediction_value = 예측)

# 고독사 실측 마지막 연도
ACTUAL_LAST_YEAR = 2023
# 현재 DB에 저장된 예측 source
LONELY_SOURCE = "rule_based"


class LonelyForecastService:
    """
    고독사 실측/예측 전용 서비스.

    - get_trend:   /api/lonely/trend
    - get_top5:    /api/lonely/top5
    - forecast_region: /api/lonely/forecast?region=...
    """

    # ----------------------------------------
    # 1) 전체 추세
    # ----------------------------------------
    def get_trend(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        전체 서울 고독사 추세.

        반환 형식:
        [
          {"year": 2017, "value": 100, "is_forecast": "N"},
          {"year": 2030, "value": 230, "is_forecast": "Y"},
          ...
        ]
        """

        # 1) 실측 (ELDERLY_STATS.target_value)
        actual_rows = (
            db.session.query(
                ElderlyStats.year,
                func.sum(ElderlyStats.target_value).label("value"),
            )
            .filter(ElderlyStats.year >= start_year)
            .filter(ElderlyStats.year <= min(end_year, ACTUAL_LAST_YEAR))
            .group_by(ElderlyStats.year)
            .all()
        )

        # 2) 예측 (PREDICTION_RESULT.prediction_value)
        forecast_rows = (
            db.session.query(
                PredictionResult.year,
                func.sum(PredictionResult.prediction_value).label("value"),
            )
            .filter(PredictionResult.year > ACTUAL_LAST_YEAR)
            .filter(PredictionResult.year >= start_year)
            .filter(PredictionResult.year <= end_year)
            .filter(PredictionResult.source == LONELY_SOURCE)
            .group_by(PredictionResult.year)
            .all()
        )

        year_map: Dict[int, Dict[str, Any]] = {}

        for year, value in actual_rows:
            year_int = int(year)
            year_map[year_int] = {
                "year": year_int,
                "value": int(value or 0),
                "is_forecast": "N",
            }

        for year, value in forecast_rows:
            year_int = int(year)
            year_map[year_int] = {
                "year": year_int,
                "value": int(value or 0),
                "is_forecast": "Y",
            }

        items = [year_map[y] for y in sorted(year_map.keys())]
        return items

    # ----------------------------------------
    # 2) TOP5 (증가율 / 증가 인원수)
    # ----------------------------------------
    def get_top5(
        self, base_year: int, target_year: int, by: str = "ratio"
    ) -> List[Dict[str, Any]]:
        """
        구별 고독사 증가 TOP5.

        base_year 는 항상 실측(ELDERLY_STATS) 기준,
        target_year 가 ACTUAL_LAST_YEAR 초과면 PREDICTION_RESULT 기반.

        반환 형식:
        [
          {
            "region": "강남구",
            "base_value": 10,
            "target_value": 25,
            "diff": 15,
            "metric_value": 1.5  # by=ratio → (diff/base)
          },
          ...
        ]
        """
        if by not in ("ratio", "absolute"):
            raise ValueError("by 파라미터는 'ratio' 또는 'absolute' 이어야 합니다.")

        # 1) base_year: ELDERLY_STATS 기준
        base_rows = (
            db.session.query(
                Region.name.label("region"),
                func.sum(ElderlyStats.target_value).label("value"),
            )
            .join(Region, ElderlyStats.region_id == Region.id)
            .filter(ElderlyStats.year == base_year)
            .group_by(Region.name)
            .all()
        )
        base_map: Dict[str, int] = {
            region: int(value or 0) for region, value in base_rows
        }

        # 2) target_year: 실측/예측 구분
        if target_year <= ACTUAL_LAST_YEAR:
            target_rows = (
                db.session.query(
                    Region.name.label("region"),
                    func.sum(ElderlyStats.target_value).label("value"),
                )
                .join(Region, ElderlyStats.region_id == Region.id)
                .filter(ElderlyStats.year == target_year)
                .group_by(Region.name)
                .all()
            )
            target_map: Dict[str, int] = {
                region: int(value or 0) for region, value in target_rows
            }
        else:
            target_rows = (
                db.session.query(
                    PredictionResult.region_name.label("region"),
                    func.sum(PredictionResult.prediction_value).label("value"),
                )
                .filter(PredictionResult.year == target_year)
                .filter(PredictionResult.source == LONELY_SOURCE)
                .group_by(PredictionResult.region_name)
                .all()
            )
            target_map = {region: int(value or 0) for region, value in target_rows}

        regions = set(base_map.keys()) | set(target_map.keys())
        items: List[Dict[str, Any]] = []

        for region in regions:
            base_val = base_map.get(region, 0)
            target_val = target_map.get(region, 0)
            diff = target_val - base_val

            if by == "ratio":
                if base_val <= 0:
                    continue
                metric = diff / base_val
            else:
                metric = diff

            items.append(
                {
                    "region": region,
                    "base_value": base_val,
                    "target_value": target_val,
                    "diff": diff,
                    "metric_value": float(metric),
                }
            )

        items.sort(key=lambda x: x["metric_value"], reverse=True)
        return items[:5]

    # ----------------------------------------
    # 3) 구별 예측 (모달)
    # ----------------------------------------
    def forecast_region(self, region_name: str) -> Dict[str, Any]:
        """
        특정 구 고독사 실측/예측.

        반환 형식:
        {
          "region": "강남구",
          "history": [{ "year": 2017, "value": 8 }, ...],
          "forecast": [{ "year": 2025, "value": 14279 }, ...],
          "message": "..."
        }
        """
        region: Region | None = Region.query.filter_by(name=region_name).first()
        if region is None:
            logger.warning(f"[LonelyForecast] Region not found: {region_name}")
            return {
                "region": region_name,
                "history": [],
                "forecast": [],
                "message": f"'{region_name}' 구를 REGION 테이블에서 찾을 수 없습니다.",
            }

        # 1) 실측: ELDERLY_STATS.target_value (<= ACTUAL_LAST_YEAR)
        actual_rows = (
            db.session.query(
                ElderlyStats.year,
                ElderlyStats.target_value,
            )
            .filter(ElderlyStats.region_id == region.id)
            .filter(ElderlyStats.year <= ACTUAL_LAST_YEAR)
            .order_by(ElderlyStats.year.asc())
            .all()
        )
        history = [
            {"year": int(year), "value": int(value or 0)}
            for year, value in actual_rows
        ]

        # 2) 예측: PREDICTION_RESULT.prediction_value (> ACTUAL_LAST_YEAR)
        forecast_rows = (
            db.session.query(
                PredictionResult.year,
                PredictionResult.prediction_value,
            )
            .filter(PredictionResult.region_name == region_name)
            .filter(PredictionResult.source == LONELY_SOURCE)
            .filter(PredictionResult.year > ACTUAL_LAST_YEAR)
            .order_by(PredictionResult.year.asc())
            .all()
        )
        forecast = [
            {"year": int(year), "value": int(value or 0)}
            for year, value in forecast_rows
        ]

        if not history and not forecast:
            logger.warning(f"[LonelyForecast] 데이터 없음 region={region_name}")
            return {
                "region": region_name,
                "history": [],
                "forecast": [],
                "message": "해당 구의 고독사 실측/예측 데이터를 찾을 수 없습니다.",
            }

        return {
            "region": region_name,
            "history": history,
            "forecast": forecast,
            "message": "ELDERLY_STATS + PREDICTION_RESULT 기반 고독사 실측/예측 데이터입니다.",
        }
