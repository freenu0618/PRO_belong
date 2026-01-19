# belong/services/lonely_forecast_service.py

from __future__ import annotations

from typing import Dict, Any

from belong.extensions import logger
from belong.repositories.lonely_forecast_repo import LonelyForecastRepository

# 고독사 실측 마지막 연도
ACTUAL_LAST_YEAR = 2023


class LonelyForecastService:
    """
    고독사 모달(한 구 상세) 서비스.

    - Repo에서 실측/예측 데이터를 가져오고
    - history / forecast 리스트로 나눠서 프론트에 전달할 구조를 만든다.
    """

    def __init__(self, repo: LonelyForecastRepository | None = None):
        # 기본적으로는 자체 레포 인스턴스를 생성하지만,
        # 나중에 DI 컨테이너에서 주입할 수도 있다.
        self.repo = repo or LonelyForecastRepository()

    def forecast_region(self, region_name: str) -> Dict[str, Any]:
        """
        특정 구(region_name)에 대한 고독사 실측/예측 타임라인을 반환.

        반환 예:
        {
          "region": "강남구",
          "history": [{"year": 2017, "value": 10}, ...],
          "forecast": [{"year": 2024, "value": 20, "source": "model"}, ...],
          "message": "..."
        }
        """
        region_name = (region_name or "").strip()

        if not region_name:
            return {
                "region": region_name,
                "history": [],
                "forecast": [],
                "message": "region 파라미터가 비어 있습니다.",
            }

        # 1) 실측: ELDERLY_STATS (<= ACTUAL_LAST_YEAR)
        history = self.repo.get_history(region_name, max_year=ACTUAL_LAST_YEAR)

        # 2) 예측: PREDICTION_RESULT (>= ACTUAL_LAST_YEAR + 1)
        #    source 필터를 쓰고 싶으면 source="model" 같은 식으로 추가할 수 있음.
        forecast = self.repo.get_forecast(
            region_name,
            min_year=ACTUAL_LAST_YEAR + 1,
        )

        # 3) 데이터가 하나도 없을 때
        if not history and not forecast:
            logger.warning(f"[LonelyForecast] 데이터 없음 region={region_name}")
            return {
                "region": region_name,
                "history": [],
                "forecast": [],
                "message": "해당 구의 고독사 실측/예측 데이터를 찾을 수 없습니다.",
            }

        # 4) 연도 기준 정렬 (Repo에서 이미 정렬했지만, 한 번 더 확실히 정렬)
        history = sorted(history, key=lambda x: x["year"])
        forecast = sorted(forecast, key=lambda x: x["year"])

        return {
            "region": region_name,
            "history": history,
            "forecast": forecast,
            "message": "ELDERLY_STATS + PREDICTION_RESULT 기반 고독사 실측/예측 데이터입니다.",
        }
