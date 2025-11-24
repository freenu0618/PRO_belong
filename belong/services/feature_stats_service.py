from typing import List, Optional, Dict

from belong.repositories.feature_stats_repo import ElderlyStatsRepository
from belong.repositories.region_repo import RegionRepository
from belong.models.feature_stats import ElderlyStats


class FeatureStatsService:
    """
    ELDERLY_STATS(노인 인구 통계)를 고수준으로 다루는 서비스 레이어.

    - Repository에서 모델을 가져온 뒤
    - 외부(예측 서비스, API)에서 쓰기 좋게 가공해서 돌려준다.
    """

    def __init__(
        self,
        elderly_stats_repo: ElderlyStatsRepository,
        region_repo: RegionRepository,
    ) -> None:
        self.elderly_stats_repo = elderly_stats_repo
        self.region_repo = region_repo

    # -----------------------------
    # 1) 단일 값 조회
    # -----------------------------
    def get_elderly_population(self, region_code: str, year: int) -> Optional[int]:
        """
        특정 구(region_code) + 연도의 노인 인구 수를 바로 int로 반환.

        예:
        - 입력: '강남구', 2021
        - 출력: 11593 (없으면 None)
        """
        stats: Optional[ElderlyStats] = (
            self.elderly_stats_repo.get_by_region_code_and_year(region_code, year)
        )
        if stats is None:
            return None

        return stats.elderly_population

    # -----------------------------
    # 2) 시계열(2017~2023 등) 조회
    # -----------------------------
    def get_time_series(
        self,
        region_code: str,
        start_year: int,
        end_year: int,
    ) -> List[Dict]:
        """
        한 구의 여러 연도(예: 2017~2023) 노인 인구 추이를 반환.

        반환 형식 예:
        [
            {"year": 2017, "elderly_population": 8502},
            {"year": 2018, "elderly_population": 8819},
            ...
        ]
        """
        region = self.region_repo.get_by_code(region_code)
        if region is None:
            return []

        stats_list: List[ElderlyStats] = self.elderly_stats_repo.get_range_by_region(
            region_id=region.id,
            start_year=start_year,
            end_year=end_year,
        )

        return [
            {
                "region_id": stats.region_id,
                "region_name": region.name,
                "year": stats.year,
                "elderly_population": stats.elderly_population,
            }
            for stats in stats_list
        ]

    # -----------------------------
    # 3) 한 구의 전체 연도 데이터 조회
    # -----------------------------
    def get_all_years_for_region(self, region_code: str) -> List[Dict]:
        """
        한 구의 모든 연도(ELDERLY_STATS에 들어있는 전체) 데이터를 조회.

        반환 형식은 get_time_series와 동일.
        """
        region = self.region_repo.get_by_code(region_code)
        if region is None:
            return []

        stats_list: List[ElderlyStats] = self.elderly_stats_repo.get_all_for_region(
            region_id=region.id
        )

        return [
            {
                "region_id": stats.region_id,
                "region_name": region.name,
                "year": stats.year,
                "elderly_population": stats.elderly_population,
            }
            for stats in stats_list
        ]
