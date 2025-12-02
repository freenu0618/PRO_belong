from belong.repositories.lonely_repo import LonelyStatsRepository
from belong.repositories.region_repo import RegionRepository
from belong.repositories.feature_stats_repo import ElderlyStatsRepository
from belong.services.feature_stats_service import FeatureStatsService
from belong.services.prediction_service import PredictionService
from belong.services.correlation_service import CorrelationService
from belong.services.population_service import PopulationService
from belong.repositories.prediction_repo import PredictionRepository
from belong.services.forecast_service import ForecastService
from belong.repositories.forecast_repo import ForecastRepository
from belong.services.elderly_service import ElderlyService
from belong.repositories.elderly_repo import SqlAlchemyElderlyHistoryRepository
from belong.services.lonely_service import LonelyService


def register_services(app):
    """
    모든 레포지토리/서비스를 생성하고 app.config['services'] 컨테이너에 저장.
    """

    # --- Repository 생성 ---
    region_repo = RegionRepository()
    elderly_stats_repo = ElderlyStatsRepository()
    lonely_stats_repo = LonelyStatsRepository()
    prediction_repo = PredictionRepository()

    # --- Service 생성 ---
    feature_stats_service = FeatureStatsService(
        elderly_stats_repo=elderly_stats_repo,
        region_repo=region_repo,
    )

    prediction_service = PredictionService(
        feature_stats_service=feature_stats_service,
        prediction_repo=prediction_repo,   # ← 생성자에서 바로 주입
    )

    lonely_service = LonelyService(
        repo=lonely_stats_repo,
        prediction_service=prediction_service,  # ← 예측 서비스 같이 주입
    )

    correlation_service = CorrelationService()
    population_service = PopulationService()
    forecast_service = ForecastService(ForecastRepository())
    elderly_service = ElderlyService(SqlAlchemyElderlyHistoryRepository())

    # --- 서비스 컨테이너 등록 ---
    services = {
        # Repos
        "region_repo": region_repo,
        "elderly_stats_repo": elderly_stats_repo,
        "lonely_repo": lonely_stats_repo,
        "prediction_repo": prediction_repo,

        # Services
        "feature_stats_service": feature_stats_service,
        "prediction_service": prediction_service,
        "lonely_service": lonely_service,
        "correlation_service": correlation_service,
        "population_service": population_service,
        "forecast_service": forecast_service,
        "elderly_service": elderly_service,
    }

    app.config["services"] = services
    return services
