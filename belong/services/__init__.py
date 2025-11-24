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
        repo: 독거노인/고령인구 히스토리를 제공하는 Repository.
              - 기본값: InMemoryElderlyHistoryRepository
              - 나중에 OracleElderlyHistoryRepository로 교체 가능
        """
        # 1) Repository DI
        self.repo: ElderlyHistoryRepository = repo or InMemoryElderlyHistoryRepository()

        # 2) 모델 로딩 (환경변수 우선, 없으면 로컬 경로)
        model_path = Config.MODEL_PATH or (
            Path(__file__).resolve().parent.parent / "ml" / "forecast_model.pkl"
        )

        try:
            self.model = joblib.load(model_path)
            logger.info(f"Model loaded successfully from {model_path}")
        except Exception as e:
            self.model = None
            logger.warning(f"Failed to load model from {model_path}. Reason: {e}")
