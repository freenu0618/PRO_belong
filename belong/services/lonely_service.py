from typing import List, Dict
from belong.repositories.lonely_repo import LonelyStatsRepository


class LonelyService:
    """
    고독사(타깃: target_value) 대시보드용 서비스.
    """

    def __init__(self, repo: LonelyStatsRepository):
        self.repo = repo

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
