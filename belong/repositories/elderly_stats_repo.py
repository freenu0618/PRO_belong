"""
ElderlyStats Repository
노인 통계 데이터 접근 계층
"""
from typing import List, Tuple, Optional
from sqlalchemy import func

from belong.extensions import db
from belong.models.feature_stats import ElderlyStats
from belong.models.region import Region


class ElderlyStatsRepository:
    """노인 통계 데이터 접근 Repository"""

    def __init__(self, session=None):
        """
        Args:
            session: SQLAlchemy 세션 (테스트 시 주입 가능)
        """
        self.session = session or db.session

    def get_available_years(self, region_name: str) -> List[int]:
        """
        특정 구의 사용 가능한 연도 조회

        Args:
            region_name: 지역명 (예: "강남구")

        Returns:
            List of available years (sorted descending)
        """
        query = (
            self.session.query(ElderlyStats.year)
            .join(Region, ElderlyStats.region_id == Region.id)
            .filter(Region.name == region_name)
            .distinct()
            .order_by(ElderlyStats.year.desc())
        )

        rows = query.all()
        return [r.year for r in rows]

    def get_stats_by_region_year(
        self, region_name: str, year: int
    ) -> Optional[ElderlyStats]:
        """
        특정 구의 특정 연도 통계 조회

        Args:
            region_name: 지역명
            year: 연도

        Returns:
            ElderlyStats 인스턴스 또는 None
        """
        query = (
            self.session.query(ElderlyStats)
            .join(Region, ElderlyStats.region_id == Region.id)
            .filter(Region.name == region_name, ElderlyStats.year == year)
        )

        return query.one_or_none()

    def get_avg_metrics(
        self, year: int, metric_fields: List[str]
    ) -> Tuple:
        """
        특정 연도의 평균 메트릭 조회

        Args:
            year: 연도
            metric_fields: 메트릭 필드 리스트 (예: ["elderly_population", "alone_household"])

        Returns:
            Tuple of average values for each metric field
        """
        query = self.session.query(
            *[func.avg(getattr(ElderlyStats, f)) for f in metric_fields]
        ).filter(ElderlyStats.year == year)

        return query.one()
