from __future__ import annotations
from typing import List, Dict, Optional
import cx_Oracle
from config import Config

from belong.extensions import db
from belong.models.elderly_history import ElderlyHistory

class ElderlyHistoryRepository:
    def get_history(self, region: str) -> Optional[List[Dict[str, int]]]:
        raise NotImplementedError

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
    SQLAlchemy ORM을 사용해서 Oracle의 ELDERLY_HISTORY 테이블에서
    데이터를 읽어오는 구현체.

    - ForecastService는 이 클래스를 repo로 주입받아서 사용 가능.
    """

    def get_history(self, region: str) -> Optional[List[Dict[str, int]]]:
        rows: List[ElderlyHistory] = (
            db.session.query(ElderlyHistory)
            .filter(ElderlyHistory.region_name == region)
            .order_by(ElderlyHistory.year)
            .all()
        )

        if not rows:
            return None

        return [
            {"year": int(row.year), "value": int(row.elderly_pop)}
            for row in rows
        ]