# belong/services/forecast_service.py

from typing import Dict, Any, Optional, List, Tuple

from belong.extensions import logger, db
from belong.models.elderly_history import ElderlyHistory
from belong.models.region import Region

# 2023년까지는 실측, 이후는 예측으로 간주
ACTUAL_LAST_YEAR = 2023


class ForecastService:
    """
    ELDERLY_HISTORY 기반 구별 노인 인구 실측/예측 조회 서비스.

    - history  : is_forecast != 'Y' 이고, year <= ACTUAL_LAST_YEAR
    - forecast : is_forecast == 'Y' 이거나, year > ACTUAL_LAST_YEAR
    """

    def __init__(self, repo: Optional[object] = None) -> None:
        """
        repo 파라미터는 과거 DI 구조 호환용으로만 남겨둔다.
        현재 구현에서는 직접 ORM 쿼리를 사용한다.
        """
        self.repo = repo

    # ------------------------------------------------------------------
    # 내부 헬퍼: 특정 구의 전체 시계열 로드 & 실측/예측 분리
    # ------------------------------------------------------------------
    def _load_region_series(self, region: str) -> Tuple[List[Dict], List[Dict]]:
        """
        ELDERLY_HISTORY + REGION 조인해서
        해당 구의 (year, elderly_population, is_forecast) 전부 가져온 뒤
        history / forecast 리스트로 나눈다.

        반환 형식:
            history  = [{"year": 2017, "value": 8502}, ...]
            forecast = [{"year": 2024, "value": 12345}, ...]
        """
        rows = (
            db.session.query(
                ElderlyHistory.year.label("year"),
                ElderlyHistory.elderly_population.label("value"),
                ElderlyHistory.is_forecast.label("is_forecast"),
            )
            .join(Region, ElderlyHistory.region_id == Region.id)
            .filter(Region.name == region)
            .order_by(ElderlyHistory.year)
            .all()
        )

        if not rows:
            return [], []

        history: List[Dict[str, int]] = []
        forecast: List[Dict[str, int]] = []

        for r in rows:
            year = int(r.year)
            value = int(r.value or 0)

            item = {
                "year": year,
                "value": value,
            }

            # 1) is_forecast 플래그 우선
            is_flag_forecast = (r.is_forecast or "N").upper() == "Y"
            # 2) 플래그가 비어 있어도 연도 기준으로 예측 구간 처리
            is_future_year = year > ACTUAL_LAST_YEAR

            if is_flag_forecast or is_future_year:
                forecast.append(item)
            else:
                history.append(item)

        # 반드시 history, forecast 둘 다 반환
        return history, forecast

    # ------------------------------------------------------------------
    # 메인 비즈니스 로직: 모달용 데이터 응답
    # ------------------------------------------------------------------
    def forecast_region(
        self,
        region: str,
        n_years: int = 0,      # 인터페이스 호환용(현재는 사용 안 함)
        horizon: str = "db",   # 인터페이스 호환용(현재는 사용 안 함)
    ) -> Dict[str, Any]:
        """
        주어진 region에 대해 ELDERLY_HISTORY 테이블에서
        실측/예측 데이터를 그대로 읽어서 반환한다.

        반환 형식:
        {
            "region": "강남구",
            "history": [
                {"year": 2017, "value": 8502},
                {"year": 2018, "value": 8819},
                ...
            ],
            "forecast": [
                {"year": 2024, "value": 12345},
                {"year": 2025, "value": 12500},
                ...
            ],
            "message": "ELDERLY_HISTORY 기반 실측/예측 데이터입니다.",
        }
        """
        logger.info(f"[REQUEST] Forecast (DB-based) region={region}")

        history, forecast = self._load_region_series(region)

        if not history and not forecast:
            logger.warning(
                f"[Forecast] ELDERLY_HISTORY에 데이터 없음: region={region}"
            )
            return {
                "region": region,
                "history": [],
                "forecast": [],
                "message": "ELDERLY_HISTORY에서 해당 구의 데이터를 찾을 수 없습니다.",
            }

        return {
            "region": region,
            "history": history,
            "forecast": forecast,
            "message": "ELDERLY_HISTORY 기반 실측/예측 데이터입니다.",
        }
