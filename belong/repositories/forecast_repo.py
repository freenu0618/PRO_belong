from __future__ import annotations
from typing import List, Dict, Optional

from belong.repositories.elderly_repo import SqlAlchemyElderlyHistoryRepository


class ForecastRepository(SqlAlchemyElderlyHistoryRepository):
    """
    ForecastService 에서 사용하는 Repo.

    현재는 ELDERLY_HISTORY 기반 SqlAlchemyElderlyHistoryRepository 를 그대로 상속해서
    get_history / get_total_trend 등 모든 메서드를 동일하게 사용한다.

    나중에 구조를 바꾸고 싶으면 여기만 교체하면 됨.
    """
    # 별도 코드 없이 상속만으로 충분
    pass
