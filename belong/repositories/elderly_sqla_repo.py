from __future__ import annotations
from typing import List, Dict, Optional

from belong.extensions import db
from belong.models.elderly_population import ElderlyHistory  # ORM 모델 (나중에 정의)
from belong.repositories.elderly_repo import ElderlyHistoryRepository


class SqlAlchemyElderlyHistoryRepository(ElderlyHistoryRepository):
    """
    SQLAlchemy ORM을 사용해서 ELDERLY_HISTORY 테이블을 읽어오는 구현체.

    - ElderlyHistory ORM 모델을 사용한다고 가정.
    - Oracle + cx_Oracle 조합은 SQLAlchemy가 내부에서 사용.
    """

    def get_history(self, region: str) -> Optional[List[Dict[str, int]]]:
        rows = (
            db.session.query(ElderlyHistory)
            .filter_by(region_name=region)
            .order_by(ElderlyHistory.year)
            .all()
        )

        if not rows:
            return None

        return [
            {"year": int(row.year), "value": int(row.elderly_pop)}
            for row in rows
        ]
