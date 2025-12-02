from typing import List, Dict
from belong.repositories.lonely_repo import LonelyStatsRepository
from belong.services.prediction_service import PredictionService
from belong.services.lonely_forecast_service import ACTUAL_LAST_YEAR


class LonelyService:
    """
    고독사(타깃: target_value) 대시보드용 서비스.
    """

    def __init__(
        self,
        repo: LonelyStatsRepository,
        prediction_service: PredictionService | None = None,
    ):
        self.repo = repo
        self.prediction_service = prediction_service

    def get_total_trend(self, start_year: int = 2017, end_year: int = 2035) -> Dict:
        items = self.repo.get_total_trend(start_year, end_year)
        return {
            "start_year": start_year,
            "end_year": end_year,
            "items": items,
        }

    def get_top5_growth(
            self,
            base_year: int,
            target_year: int,
            by: str = "ratio",
    ) -> Dict:
        """
        base_year → target_year 사이 증가율/증가량 기준 TOP5 구.
        - target_year가 ACTUAL_LAST_YEAR(예: 2023)보다 크면,
          PredictionService를 사용해 해당 연도의 예측값을 먼저 생성한다.
        """

        # 1) 미래 연도에 대해서는 예측값을 먼저 보장
        if target_year > ACTUAL_LAST_YEAR:
            if self.prediction_service is None:
                raise RuntimeError(
                    "미래 연도 고독사 TOP5를 계산하려면 PredictionService가 필요합니다."
                )

            # 모든 구에 대해 target_year 예측을 보장 (없으면 생성)
            self.prediction_service.ensure_predictions_for_year(target_year)

        # 2) 그 다음 기존 로직대로 repo에서 (base, target) 값을 가져온다.
        rows = self.repo.get_region_values_for_years(base_year, target_year)

        results: List[Dict] = []
        for info in rows:
            base_val = info["base_value"]
            target_val = info["target_value"]
            if base_val is None or target_val is None:
                continue

            diff = target_val - base_val
            if by == "ratio":
                if base_val == 0:
                    continue
                metric_value = diff / base_val
            else:
                metric_value = diff

            results.append(
                {
                    **info,
                    "diff": diff,
                    "metric_value": metric_value,
                }
            )

        results.sort(key=lambda x: x["metric_value"], reverse=True)
        top5 = results[:5]

        return {
            "base_year": base_year,
            "target_year": target_year,
            "by": by,
            "items": top5,
        }

