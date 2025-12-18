from __future__ import annotations
from typing import List, Dict, Optional
import oracledb as cx_Oracle
from config import Config
from sqlalchemy import func

from belong.extensions import db
from belong.models.elderly_history import ElderlyHistory
from belong.models.region import Region

class ElderlyHistoryRepository:
    def get_total_trend(self, start_year: int, end_year: int) -> List[Dict]:
        """
        전체(25개 구 합계) 연도별 노인 인구 추세.
        year, is_forecast, total_elderly_population 을 반환.
        """
        q = (
            db.session.query(
                ElderlyHistory.year.label("year"),
                ElderlyHistory.is_forecast.label("is_forecast"),
                func.sum(ElderlyHistory.elderly_population).label("total_elderly_population"),
            )
            .filter(ElderlyHistory.year.between(start_year, end_year))
            .group_by(ElderlyHistory.year, ElderlyHistory.is_forecast)
            .order_by(ElderlyHistory.year)
        )

        rows = q.all()
        return [
            {
                "year": int(r.year),
                "is_forecast": (r.is_forecast == "Y"),
                "total_elderly_population": int(r.total_elderly_population or 0),
            }
            for r in rows
        ]

    def get_region_snapshot(self, year: int) -> List[Dict]:
        """
        특정 연도(year)의 구별 노인 인구 스냅샷.
        (실측/예측 상관없이 ELDERLY_HISTORY에서 year에 해당하는 데이터 한 번에 조회)
        """
        q = (
            db.session.query(
                Region.id.label("region_id"),
                Region.name.label("region"),
                ElderlyHistory.year.label("year"),
                ElderlyHistory.elderly_population.label("elderly_population"),
                ElderlyHistory.is_forecast.label("is_forecast"),
            )
            .join(ElderlyHistory, ElderlyHistory.region_id == Region.id)
            .filter(ElderlyHistory.year == year)
            .order_by(Region.name)
        )

        rows = q.all()
        return [
            {
                "region_id": int(r.region_id),
                "region": str(r.region).strip(),
                "year": int(r.year),
                "elderly_population": int(r.elderly_population or 0),
                "is_forecast": (r.is_forecast == "Y"),
            }
            for r in rows
        ]

    def get_region_values_for_years(self, years: List[int]) -> List[Dict]:
        """
        base_year / target_year용 데이터를 한 번에 가져오기 위한 헬퍼.
        year in (base_year, target_year) 인 행들을 REGION과 조인해서 리턴.
        """
        q = (
            db.session.query(
                Region.id.label("region_id"),
                Region.name.label("region"),
                ElderlyHistory.year.label("year"),
                ElderlyHistory.elderly_population.label("elderly_population"),
                ElderlyHistory.is_forecast.label("is_forecast"),
            )
            .join(ElderlyHistory, ElderlyHistory.region_id == Region.id)
            .filter(ElderlyHistory.year.in_(years))
        )

        rows = q.all()
        return [
            {
                "region_id": int(r.region_id),
                "region": str(r.region).strip(),
                "year": int(r.year),
                "elderly_population": int(r.elderly_population or 0),
                "is_forecast": (r.is_forecast == "Y"),
            }
            for r in rows
        ]

class InMemoryElderlyHistoryRepository(ElderlyHistoryRepository):
    def __init__(self) -> None:
        self.region_history: Dict[str, List[Dict[str, int]]] = {
            "강남구": [
                {"year": 2019, "value": 12000},
                {"year": 2020, "value": 12600},
                {"year": 2021, "value": 13000},
            ],
            "종로구": [
                {"year": 2019, "value": 5000},
                {"year": 2020, "value": 5200},
                {"year": 2021, "value": 5400},
            ],
            "동작구": [
                {"year": 2019, "value": 7000},
                {"year": 2020, "value": 7300},
                {"year": 2021, "value": 7600},
            ],
        }

    def get_history(self, region: str) -> Optional[List[Dict[str, int]]]:
        return self.region_history.get(region)
    def get_total_trend(self, start_year: int, end_year: int) -> List[Dict]:
        raise NotImplementedError

    def get_region_snapshot(self, year: int) -> List[Dict]:
        raise NotImplementedError

    def get_region_values_for_years(self, years: List[int]) -> List[Dict]:
        raise NotImplementedError

class OracleElderlyHistoryRepository(ElderlyHistoryRepository):
    """
    Oracle DB에서 ELDERLY_HISTORY 테이블을 읽어오는 구현체.

    - cx_Oracle.SessionPool을 사용해서 커넥션 풀을 만든다.
    - ForecastService는 이 Repo를 주입받아서 사용한다.
    """

    def __init__(
        self,
        user: str | None = None,
        password: str | None = None,
        dsn: str | None = None,
        min_conn: int = 1,
        max_conn: int = 4,
        increment: int = 1,
    ) -> None:
        self.user = user or Config.ORACLE_USER
        self.password = password or Config.ORACLE_PASSWORD
        self.dsn = dsn or Config.ORACLE_DSN

        self.pool = cx_Oracle.SessionPool(
            user=self.user,
            password=self.password,
            dsn=self.dsn,
            min=min_conn,
            max=max_conn,
            increment=increment,
            threaded=True,
            getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT,
        )

    def get_history(self, region: str) -> Optional[List[Dict[str, int]]]:
        conn = self.pool.acquire()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT YEAR, ELDERLY_POP
                FROM ELDERLY_HISTORY
                WHERE REGION_NAME = :region
                ORDER BY YEAR
                """,
                region=region,
            )
            rows = cur.fetchall()
        finally:
            self.pool.release(conn)

        if not rows:
            return None

        return [
            {"year": int(year), "value": int(value)}
            for year, value in rows
        ]

class SqlAlchemyElderlyHistoryRepository(ElderlyHistoryRepository):
    """
    SQLAlchemy ORM을 사용해서 Oracle 의 ELDERLY_HISTORY/REGION 을 조회하는 구현체.
    """

    # ---- ForecastService 용: 타임시리즈 ----
    def get_history(self, region: str) -> Optional[List[Dict[str, int]]]:
        rows: List[ElderlyHistory] = (
            db.session.query(ElderlyHistory)
            .join(Region, ElderlyHistory.region_id == Region.id)
            .filter(Region.name == region)
            .order_by(ElderlyHistory.year)
            .all()
        )

        if not rows:
            return None

        return [
            {
                "year": int(row.year),
                "value": int(row.elderly_population or 0),
            }
            for row in rows
        ]

    # ---- ElderlyService 용: 전체 추세 ----
    def get_total_trend(self, start_year: int, end_year: int) -> List[Dict]:
        q = (
            db.session.query(
                ElderlyHistory.year.label("year"),
                ElderlyHistory.is_forecast.label("is_forecast"),
                func.sum(ElderlyHistory.elderly_population).label(
                    "total_elderly_population"
                ),
            )
            .filter(ElderlyHistory.year.between(start_year, end_year))
            .group_by(ElderlyHistory.year, ElderlyHistory.is_forecast)
            .order_by(ElderlyHistory.year)
        )

        rows = q.all()
        return [
            {
                "year": int(r.year),
                "is_forecast": (r.is_forecast == "Y"),
                "total_elderly_population": int(r.total_elderly_population or 0),
            }
            for r in rows
        ]

    # ---- ElderlyService 용: 특정 연도 구별 스냅샷 ----
    def get_region_snapshot(self, year: int) -> List[Dict]:
        q = (
            db.session.query(
                Region.id.label("region_id"),
                Region.name.label("region"),
                ElderlyHistory.year.label("year"),
                ElderlyHistory.elderly_population.label("elderly_population"),
                ElderlyHistory.is_forecast.label("is_forecast"),
            )
            .join(ElderlyHistory, ElderlyHistory.region_id == Region.id)
            .filter(ElderlyHistory.year == year)
            .order_by(Region.name)
        )

        rows = q.all()
        return [
            {
                "region_id": int(r.region_id),
                "region": str(r.region).strip(),
                "year": int(r.year),
                "elderly_population": int(r.elderly_population or 0),
                "is_forecast": (r.is_forecast == "Y"),
            }
            for r in rows
        ]

    # ---- ElderlyService 용: base/target 연도 한 번에 조회 ----
    def get_region_values_for_years(self, years: List[int]) -> List[Dict]:
        q = (
            db.session.query(
                Region.id.label("region_id"),
                Region.name.label("region"),
                ElderlyHistory.year.label("year"),
                ElderlyHistory.elderly_population.label("elderly_population"),
                ElderlyHistory.is_forecast.label("is_forecast"),
            )
            .join(ElderlyHistory, ElderlyHistory.region_id == Region.id)
            .filter(ElderlyHistory.year.in_(years))
        )

        rows = q.all()
        return [
            {
                "region_id": int(r.region_id),
                "region": str(r.region).strip(),
                "year": int(r.year),
                "elderly_population": int(r.elderly_population or 0),
                "is_forecast": (r.is_forecast == "Y"),
            }
            for r in rows
        ]