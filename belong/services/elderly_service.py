from typing import List, Dict

from belong.repositories.elderly_repo import ElderlyHistoryRepository


class ElderlyService:
    """
    노인 인구(실측+예측) 대시보드용 서비스 계층.
    """

    def __init__(self, elderly_repo: ElderlyHistoryRepository):
        self.elderly_repo = elderly_repo

    # 1) 추세 그래프용
    def get_total_trend(self, start_year: int = 2017, end_year: int = 2035) -> Dict:
        """
        전체 연도별 노인 인구 추세 데이터.
        프론트에서 라인차트로 바로 쓸 수 있게 정제해서 반환.
        """
        trend_rows = self.elderly_repo.get_total_trend(start_year, end_year)

        # 정렬 보장
        trend_rows = sorted(trend_rows, key=lambda x: x["year"])

        return {
            "start_year": start_year,
            "end_year": end_year,
            "items": trend_rows,
        }

    # 2) TOP5용
    def get_top5_growth(
        self,
        base_year: int,
        target_year: int,
        by: str = "ratio",  # "ratio" or "absolute"
    ) -> Dict:
        """
        base_year vs target_year 사이의 증가율/증가인원 TOP5.
        - by="ratio"    : (target - base) / base
        - by="absolute" : (target - base)
        """
        rows = self.elderly_repo.get_region_values_for_years([base_year, target_year])

        # region 기준으로 base/target 묶기
        data = {}
        for r in rows:
            region = r["region"]
            year = r["year"]
            val = r["elderly_population"]

            if region not in data:
                data[region] = {
                    "region_id": r["region_id"],
                    "region": region,
                    "base_year": base_year,
                    "base_value": None,
                    "target_year": target_year,
                    "target_value": None,
                }

            if year == base_year:
                data[region]["base_value"] = val
            elif year == target_year:
                data[region]["target_value"] = val

        results: List[Dict] = []
        for region, info in data.items():
            base_val = info["base_value"]
            target_val = info["target_value"]

            # 둘 중 하나라도 없으면 스킵
            if base_val is None or target_val is None:
                continue

            diff = target_val - base_val
            if by == "ratio":
                if base_val == 0:
                    # 0에서 시작하면 ratio 계산이 애매하니 스킵 or 별도 처리
                    continue
                metric_value = diff / base_val
            else:
                # absolute
                metric_value = diff

            results.append(
                {
                    "region_id": info["region_id"],
                    "region": region,
                    "base_year": base_year,
                    "base_value": base_val,
                    "target_year": target_year,
                    "target_value": target_val,
                    "diff": diff,
                    "metric_value": metric_value,
                }
            )

        # metric_value 기준 내림차순 정렬 후 TOP5
        results.sort(key=lambda x: x["metric_value"], reverse=True)
        top5 = results[:5]

        return {
            "base_year": base_year,
            "target_year": target_year,
            "by": by,
            "items": top5,
        }

    # 3) 연도별 구별 예측(테이블/차트용)
    def get_region_snapshot(self, year: int) -> Dict:
        """
        특정 연도의 구별 노인 인구 리스트 (실측/예측 포함).
        """
        items = self.elderly_repo.get_region_snapshot(year)
        return {
            "year": year,
            "items": items,
        }
