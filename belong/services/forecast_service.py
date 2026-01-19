# belong/services/forecast_service.py

from __future__ import annotations

from typing import List, Dict, Any

from belong.extensions import logger
from belong.models.region import Region
from belong.repositories.elderly_history_repo import ElderlyHistoryRepository

# 2023년까지는 실측, 이후는 예측으로 취급
ACTUAL_LAST_YEAR = 2023


class ForecastService:
    """
    ELDERLY_HISTORY 기반 노인 인구 실측/예측 서비스.

    - get_total_trend: /api/elderly/trend
    - get_top5:       /api/elderly/top5
    - forecast_region:/api/elderly/forecast/<region>
    """

    def __init__(self, elderly_repo: ElderlyHistoryRepository = None):
        """
        Args:
            elderly_repo: ElderlyHistoryRepository 인스턴스 (DI)
        """
        self.elderly_repo = elderly_repo or ElderlyHistoryRepository()

    def get_total_trend(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        전체 서울 노인 인구 추세.

        반환 형식:
        [
          {
            "year": 2017,
            "total_elderly_population": 12345,
            "is_forecast": "N"
          },
          ...
        ]
        """
        # Repository를 통한 데이터 접근
        rows = self.elderly_repo.get_total_trend(start_year, end_year)

        result: List[Dict[str, Any]] = []
        for year, total in rows:
            year_int = int(year)
            total_int = int(total or 0)
            result.append(
                {
                    "year": year_int,
                    "total_elderly_population": total_int,
                    "is_forecast": "Y" if year_int > ACTUAL_LAST_YEAR else "N",
                }
            )

        return result

    # --------------------------------------------------
    # TOP5 (증가율 / 증가 인원수)
    # --------------------------------------------------
    def get_top5(
        self, base_year: int, target_year: int, by: str = "ratio"
    ) -> List[Dict[str, Any]]:
        """
        구별 노인 인구 증가 TOP5.

        반환 형식:
        [
          {
            "region": "강남구",
            "base_value": 1234,
            "target_value": 2345,
            "diff": 1111,
            "metric_value": 0.35  # ratio일 때는 비율(0.35 → 35%)
          },
          ...
        ]
        """
        if by not in ("ratio", "absolute"):
            raise ValueError("by 파라미터는 'ratio' 또는 'absolute' 이어야 합니다.")

        # Repository를 통한 데이터 접근
        rows = self.elderly_repo.get_top5_regions(base_year, target_year)

        items: List[Dict[str, Any]] = []
        for region, base_val, target_val in rows:
            base_val = int(base_val or 0)
            target_val = int(target_val or 0)
            diff = target_val - base_val

            if by == "ratio":
                if base_val <= 0:
                    # 기준 값이 0이면 증가율 계산 불가 → 스킵
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

        # metric_value 기준 내림차순 정렬 후 TOP5
        items.sort(key=lambda x: x["metric_value"], reverse=True)
        return items[:5]

    # --------------------------------------------------
    # 구별 예측 (모달)
    # --------------------------------------------------
    def forecast_region(self, region_name: str) -> Dict[str, Any]:
        """
        특정 구의 노인 인구 실측/예측 시계열.

        반환 형식:
        {
          "region": "강남구",
          "history": [ {"year": 2017, "value": 8502}, ... ],
          "forecast": [ {"year": 2024, "value": 14123}, ... ],
          "message": "ELDERLY_HISTORY 기반 실측/예측 데이터입니다."
        }
        """
        # Region 조회 (TODO: 향후 RegionRepository로 이동 검토)
        region: Region | None = Region.query.filter_by(name=region_name).first()
        if region is None:
            logger.warning(f"[ForecastService] Region not found: {region_name}")
            return {
                "region": region_name,
                "history": [],
                "forecast": [],
                "message": f"'{region_name}' 구를 REGION 테이블에서 찾을 수 없습니다.",
            }

        # Repository를 통한 데이터 접근
        rows = self.elderly_repo.get_region_forecast(region.id)

        history: List[Dict[str, Any]] = []
        forecast: List[Dict[str, Any]] = []

        for year, value, is_fc in rows:
            item = {
                "year": int(year),
                "value": int(value or 0),
            }

            flag = (is_fc or "N").upper()
            if flag == "Y" or int(year) > ACTUAL_LAST_YEAR:
                forecast.append(item)
            else:
                history.append(item)

        if not history and not forecast:
            return {
                "region": region_name,
                "history": [],
                "forecast": [],
                "message": "ELDERLY_HISTORY에서 해당 구의 데이터를 찾을 수 없습니다.",
            }

        return {
            "region": region_name,
            "history": history,
            "forecast": forecast,
            "message": "ELDERLY_HISTORY 기반 실측/예측 데이터입니다.",
        }
