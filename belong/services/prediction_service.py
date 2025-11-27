from typing import Optional, Dict, List

from belong.services.feature_stats_service import FeatureStatsService
from belong.repositories.prediction_repo import PredictionRepository
from belong.ml.model_loader import load_model
from belong.extensions import logger


class PredictionService:
    """
    ELDERLY_STATS + ML 모델(or 규칙 기반)을 이용해
    특정 구(region)와 연도(year)에 대한 예측값을 반환하고,
    필요하면 PREDICTION_RESULT 테이블에 저장하는 서비스.
    """

    def __init__(
        self,
        feature_stats_service: FeatureStatsService,
        prediction_repo: Optional[PredictionRepository] = None,
    ) -> None:
        self.feature_stats_service = feature_stats_service
        self.prediction_repo = prediction_repo

        # 모델 로딩 (실패해도 앱은 뜨고, rule-based로 fallback)
        try:
            self.model = load_model()
            logger.info("Forecast model loaded successfully via model_loader.load_model()")
        except Exception as e:
            self.model = None
            logger.warning(
                "Failed to load forecast model. Fallback to rule-based prediction. Reason: %s",
                e,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def predict(self, region_name: str, year: int) -> Optional[Dict]:
        """
        특정 구 + 연도에 대한 예측값 반환.
        반환 형식 예:
        {
          "region": "강남구",
          "year": 2025,
          "prediction": 12345.0,
          "source": "model" or "rule_based",
          "history": [
            {"year": 2017, "elderly_population": 8502},
            ...
          ]
        }
        """
        features = self._build_features(region_name, year)
        if features is None:
            logger.warning("[PredictionService] No history found for region=%s", region_name)
            return None

        history = features["history"]
        y_pred = None
        source = "rule_based"

        # 1) 모델 예측 시도
        if self.model is not None and hasattr(self.model, "predict"):
            try:
                X = self._to_model_input(features)
                y_pred = float(self.model.predict(X)[0])
                source = "model"
            except Exception as e:
                logger.warning(
                    "[PredictionService] Model prediction failed. "
                    "Fallback to rule-based. Reason: %s",
                    e,
                )

        # 2) 모델 없거나 실패하면 rule-based
        if y_pred is None:
            y_pred = float(
                self._rule_based_forecast(
                    last_value=features["last_value"],
                    years_ahead=features["years_ahead"],
                )
            )
            source = "rule_based"

        return {
            "region": region_name,
            "year": year,
            "prediction": y_pred,
            "source": source,
            "history": history,
        }

    def predict_and_store(self, region_name: str, year: int) -> Optional[Dict]:
        """
        예측을 수행하고, prediction_repo가 설정되어 있으면 DB에 저장까지 수행.
        """
        result = self.predict(region_name, year)
        if result is None:
            return None

        if self.prediction_repo is not None:
            self.prediction_repo.save(
                region=result["region"],
                year=result["year"],
                value=result["prediction"],
                source=result["source"],
            )
        else:
            logger.warning("[PredictionService] prediction_repo is None; skipping save()")

        return result

    # ------------------------------------------------------------------
    # 내부 헬퍼들
    # ------------------------------------------------------------------
    def _build_features(self, region_name: str, target_year: int) -> Optional[Dict]:
        """
        FeatureStatsService를 이용해 해당 region의 시계열(history)을 가져오고,
        예측에 사용할 간단한 feature를 만든다.
        """
        # ELDERLY_STATS에서 해당 구의 전체 연도 데이터 조회
        history_raw: List[Dict] = self.feature_stats_service.get_all_years_for_region(
            region_code=region_name
        )
        if not history_raw:
            return None

        # year 기준 오름차순 정렬
        history_sorted = sorted(history_raw, key=lambda x: x["year"])

        # (연도, 노인 인구)만 history로 정제
        history = [
            {
                "year": int(row["year"]),
                "elderly_population": int(row["elderly_population"]),
            }
            for row in history_sorted
        ]

        first = history[0]
        last = history[-1]
        first_year = first["year"]
        last_year = last["year"]
        first_value = first["elderly_population"]
        last_value = last["elderly_population"]

        # 단순 추세(기울기) 계산 (최소 2개 이상일 때만)
        if len(history) >= 2 and last_year != first_year:
            slope = (last_value - first_value) / (last_year - first_year)
        else:
            slope = 0.0

        years_ahead = max(0, target_year - last_year)

        return {
            "history": history,
            "first_year": first_year,
            "last_year": last_year,
            "first_value": first_value,
            "last_value": last_value,
            "slope": slope,
            "target_year": target_year,
            "years_ahead": years_ahead,
        }

    def _to_model_input(self, features: Dict):
        """
        ML 모델이 기대하는 입력 형식으로 feature를 변환.
        현재는 예시로 아래 4개 feature를 사용:
        - target_year
        - last_value
        - slope
        - years_ahead
        """
        return [[
            features["target_year"],
            features["last_value"],
            features["slope"],
            features["years_ahead"],
        ]]

    def _rule_based_forecast(self, last_value: int, years_ahead: int) -> int:
        """
        모델이 없거나, 예측에 실패한 경우 사용할 규칙 기반 예측.
        - 기본: 연 3% 증가 가정
        """
        if years_ahead <= 0:
            return int(last_value)

        growth_rate = 0.03  # 3% 증가
        value = float(last_value)
        for _ in range(years_ahead):
            value *= (1 + growth_rate)
        return int(round(value))
