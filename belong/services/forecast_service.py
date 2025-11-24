import joblib
from pathlib import Path
from typing import Dict, Any, Optional

from config import Config
from belong.extensions import logger
from belong.repositories.elderly_repo import (
    ElderlyHistoryRepository,
    InMemoryElderlyHistoryRepository,
)


class ForecastService:
    def __init__(self, repo: Optional[ElderlyHistoryRepository] = None) -> None:
        """
        repo: 독거노인/고령인구 히스토리를 제공하는 Repository
              - 기본값: InMemoryElderlyHistoryRepository
              - 나중에 Oracle/SQLAlchemy 기반 Repo로 교체 예정
        """
        # 1) Repository DI
        self.repo: ElderlyHistoryRepository = (
            repo if repo is not None else InMemoryElderlyHistoryRepository()
        )

        # 2) 모델 로딩 (환경변수 우선, 없으면 로컬 pkl 경로)
        model_path = Config.MODEL_PATH or (
            Path(__file__).resolve().parent.parent / "ml" / "forecast_model.pkl"
        )

        try:
            self.model = joblib.load(model_path)
            logger.info(f"Model loaded successfully from {model_path}")
        except Exception as e:
            self.model = None
            logger.warning(f"Failed to load model from {model_path}. Reason: {e}")

    # --- 내부 헬퍼: history 조회 ---

    def _get_history(self, region: str):
        """
        v0.2: InMemoryElderlyHistoryRepository에서 조회.
        v0.3~: Oracle/SQLAlchemy 기반 Repo로 교체 가능.
        """
        return self.repo.get_history(region)

    # --- 메인 비즈니스 로직: 단기/장기 예측 ---

    def forecast_region(
        self,
        region: str,
        n_years: int = 2,
        horizon: str = "short",
    ) -> Dict[str, Any]:
        """
        단기/장기 horizon을 고려한 예측 서비스 메소드.

        - 지금은 모델이 없어도 dummy 규칙으로 forecast를 항상 채운다.
        - 나중에 Oracle/실제 모델을 붙여도 이 함수 시그니처는 그대로 유지.
        """
        logger.info(
            f"[REQUEST] Forecast service called "
            f"for region={region}, years={n_years}, horizon={horizon}"
        )

        history = self._get_history(region)

        if history is None:
            logger.warning(f"No history data found for region: {region}")
            return {
                "region": region,
                "history": None,
                "forecast": None,
                "message": "No history data available for this region.",
            }

        last_year = history[-1]["year"]
        last_value = history[-1]["value"]

        # 1) 실제 모델이 있는 경우 → 나중에 여기서 model.predict(...) 사용
        if self.model is not None:
            logger.info(
                "Model is loaded. (Currently using dummy values) "
                f"horizon={horizon}, n_years={n_years}"
            )
            # TODO: 진짜 예측으로 교체할 자리
            forecast_values = [int(last_value * 1.05)] * n_years  # placeholder
        else:
            # 2) 모델이 없는 경우 → horizon별 증가율로 dummy 예측
            if horizon == "short":
                growth_rate = 0.03  # 단기: 3% 증가
            elif horizon == "long":
                growth_rate = 0.02  # 장기: 2% 완만 증가
            else:
                growth_rate = 0.025  # fallback

            forecast_values = []
            value = last_value
            for _ in range(n_years):
                value = int(value * (1 + growth_rate))
                forecast_values.append(value)

        forecast = [
            {"year": last_year + i + 1, "value": forecast_values[i]}
            for i in range(n_years)
        ]

        return {
            "region": region,
            "history": history,
            "forecast": forecast,
            "message": (
                "Dummy forecast (model not loaded)"
                if self.model is None
                else "Model forecast (dummy values)"
            ),
        }