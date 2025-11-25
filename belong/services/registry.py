from belong.repositories.region_repo import RegionRepository
from belong.repositories.feature_stats_repo import ElderlyStatsRepository
from belong.services.feature_stats_service import FeatureStatsService
from belong.services.prediction_service import PredictionService
from belong.services.correlation_service import CorrelationService
from belong.services.population_service import PopulationService


def register_services(app):
    """
    모든 레포지토리/서비스를 생성하고 app.config['services'] 컨테이너에 저장.
    """

    # --- Repository 생성 ---
    region_repo = RegionRepository()
    elderly_stats_repo = ElderlyStatsRepository()

    # --- Service 생성 ---
    feature_stats_service = FeatureStatsService(
        elderly_stats_repo=elderly_stats_repo,
        region_repo=region_repo,
    )

    prediction_service = PredictionService(
        feature_stats_service=feature_stats_service
    )

    correlation_service = CorrelationService()
    population_service = PopulationService()

    # --- 서비스 컨테이너 등록 ---
    services = {
        "region_repo": region_repo,
        "elderly_stats_repo": elderly_stats_repo,
        "feature_stats_service": feature_stats_service,
        "prediction_service": prediction_service,
        "correlation_service": correlation_service,
        "population_service": population_service,
    }

    app.config["services"] = services
    return services
