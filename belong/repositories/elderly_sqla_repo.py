from __future__ import annotations
from typing import List, Dict, Optional, Tuple

from belong.extensions import db
from belong.models.elderly_history import ElderlyHistory
from belong.models.region import Region
from belong.repositories.elderly_repo import ElderlyHistoryRepository


class SqlAlchemyElderlyHistoryRepository(ElderlyHistoryRepository):
    """
    SQLAlchemy ORM을 사용해서 ELDERLY_HISTORY 테이블을 읽어오는 구현체.

    - REGION 테이블과 조인해서 Region.name 으로 필터링한다.
    - elderly_population 컬럼을 사용해 노인 인구 값을 가져온다.
    """

    def get_history(self, region: str) -> Optional[List[Dict[str, int]]]:
        """
        주어진 구(region)에 대한 전체 시계열(실측/예측 구분 없이)을 반환한다.

        반환 형식:
        [
            {"year": 2017, "value": 12345},
            {"year": 2018, "value": 12567},
            ...
        ]
        """
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
                "year": int(r.year),
                "value": int(r.elderly_population or 0),
            }
            for r in rows
        ]

    def get_split_history(
        self,
        region: str,
    ) -> Optional[Tuple[List[Dict], List[Dict]]]:
        """
        ELDERLY_HISTORY에서 region별 실측/예측을 분리해서 가져온다.

        - history : is_forecast != 'Y'
        - forecast: is_forecast == 'Y'

        반환 형식:
        (
            [  # history
                {"year": 2017, "value": 12345},
                {"year": 2018, "value": 12567},
                ...
            ],
            [  # forecast
                {"year": 2024, "value": 14000},
                {"year": 2025, "value": 14200},
                ...
            ]
        )
        """
        rows: List[ElderlyHistory] = (
            db.session.query(ElderlyHistory)
            .join(Region, ElderlyHistory.region_id == Region.id)
            .filter(Region.name == region)
            .order_by(ElderlyHistory.year)
            .all()
        )

        if not rows:
            return None

        history: List[Dict] = []
        forecast: List[Dict] = []

        for r in rows:
            item = {
                "year": int(r.year),
                "value": int(r.elderly_population or 0),
            }

            # is_forecast 컬럼이 None 이거나 소문자여도 안전하게 처리
            if (r.is_forecast or "N").upper() == "Y":
                forecast.append(item)
            else:
                history.append(item)

        return history, forecast
