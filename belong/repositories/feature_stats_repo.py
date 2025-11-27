from typing import List, Optional

from belong.extensions import db
from belong.models.region import Region
from belong.models.feature_stats import ElderlyStats


class ElderlyStatsRepository:
    """ELDERLY_STATS(= feature_stats) 조회 전용 Repository"""

    def get_by_region_and_year(self, region_id: int, year: int) -> Optional[ElderlyStats]:
        """특정 구 + 연도 1건 조회"""
        return (
            ElderlyStats.query
            .filter_by(region_id=region_id, year=year)
            .one_or_none()
        )

    def get_by_region_code_and_year(self, region_code: str, year: int) -> Optional[ElderlyStats]:
        """
        '강남구' 같은 region_code로 바로 찾고 싶을 때 사용.
        1) Region에서 code로 구를 찾고
        2) 그 id를 이용해 ElderlyStats 조회
        """
        region = Region.query.filter_by(code=region_code).one_or_none()
        if region is None:
            return None

        return (
            ElderlyStats.query
            .filter_by(region_id=region.id, year=year)
            .one_or_none()
        )

    def get_range_by_region(self, region_id: int, start_year: int, end_year: int) -> List[ElderlyStats]:
        """한 구의 여러 연도 구간 조회 (예: 2017~2023)"""
        return (
            ElderlyStats.query
            .filter(
                ElderlyStats.region_id == region_id,
                ElderlyStats.year >= start_year,
                ElderlyStats.year <= end_year,
            )
            .order_by(ElderlyStats.year)
            .all()
        )

    def get_all_for_region(self, region_id: int) -> List[ElderlyStats]:
        """한 구의 전체 연도 데이터 (정렬 포함)"""
        return (
            ElderlyStats.query
            .filter_by(region_id=region_id)
            .order_by(ElderlyStats.year)
            .all()
        )

    def get_by_region_name_and_year(self, region_name: str, year: int) -> Optional[ElderlyStats]:
        """
        '강남구' 같은 지역 이름 + 연도로 ElderlyStats 1건 조회
        """
        region = Region.query.filter_by(name=region_name).one_or_none()
        if region is None:
            return None

        return (
            ElderlyStats.query
            .filter_by(region_id=region.id, year=year)
            .one_or_none()
        )