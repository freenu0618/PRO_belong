"""
ElderlyHistory Repository
노인 인구 이력 데이터 접근 계층
"""
from typing import List, Tuple, Any
from sqlalchemy import func, case

from belong.extensions import db
from belong.models.elderly_history import ElderlyHistory
from belong.models.region import Region


class ElderlyHistoryRepository:
    """노인 인구 이력 데이터 접근 Repository"""

    def __init__(self, session=None):
        """
        Args:
            session: SQLAlchemy 세션 (테스트 시 주입 가능)
        """
        self.session = session or db.session

    def get_total_trend(self, start_year: int, end_year: int) -> List[Tuple[int, int]]:
        """
        전체 서울 노인 인구 추세 조회

        Args:
            start_year: 시작 연도
            end_year: 종료 연도

        Returns:
            List of (year, total_elderly_population) tuples
        """
        query = (
            self.session.query(
                ElderlyHistory.year.label("year"),
                func.sum(ElderlyHistory.elderly_population).label("total_elderly_population"),
            )
            .filter(ElderlyHistory.year >= start_year)
            .filter(ElderlyHistory.year <= end_year)
            .group_by(ElderlyHistory.year)
            .order_by(ElderlyHistory.year.asc())
        )

        return query.all()

    def get_top5_regions(
        self, base_year: int, target_year: int
    ) -> List[Tuple[str, int, int]]:
        """
        구별 노인 인구 증가 TOP5 데이터 조회

        Args:
            base_year: 기준 연도
            target_year: 목표 연도

        Returns:
            List of (region_name, base_value, target_value) tuples
        """
        base_case = case(
            (ElderlyHistory.year == base_year, ElderlyHistory.elderly_population),
            else_=0,
        )
        target_case = case(
            (ElderlyHistory.year == target_year, ElderlyHistory.elderly_population),
            else_=0,
        )

        query = (
            self.session.query(
                Region.name.label("region"),
                func.sum(base_case).label("base_value"),
                func.sum(target_case).label("target_value"),
            )
            .join(Region, ElderlyHistory.region_id == Region.id)
            .group_by(Region.name)
        )

        return query.all()

    def get_region_forecast(self, region_id: int) -> List[Tuple[int, int, str]]:
        """
        특정 구의 실측/예측 시계열 조회

        Args:
            region_id: 지역 ID

        Returns:
            List of (year, elderly_population, is_forecast) tuples
        """
        query = (
            self.session.query(
                ElderlyHistory.year,
                ElderlyHistory.elderly_population,
                ElderlyHistory.is_forecast,
            )
            .filter(ElderlyHistory.region_id == region_id)
            .order_by(ElderlyHistory.year.asc())
        )

        return query.all()
