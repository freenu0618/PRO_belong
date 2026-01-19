from belong.repositories.lonely_repo import LonelyStatsRepository
from belong.repositories.region_repo import RegionRepository
from belong.repositories.feature_stats_repo import ElderlyStatsRepository as FeatureStatsRepo
from belong.repositories.elderly_history_repo import ElderlyHistoryRepository
from belong.repositories.elderly_stats_repo import ElderlyStatsRepository as ElderlyStatsRepo
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
from belong.services.region_risk_service import RegionRiskService


def register_services(app):
    """
    모든 레포지토리/서비스를 생성하고 app.config['services'] 컨테이너에 저장.
    """

    # --- Repository 생성 ---
    region_repo = RegionRepository()
    feature_stats_repo = FeatureStatsRepo()  # Feature stats용 (기존)
    elderly_history_repo = ElderlyHistoryRepository()  # 노인 인구 이력용 (신규)
    elderly_stats_repo = ElderlyStatsRepo()  # 노인 통계용 (신규)
    lonely_stats_repo = LonelyStatsRepository()
    prediction_repo = PredictionRepository()

    # --- Service 생성 ---
    feature_stats_service = FeatureStatsService(
        elderly_stats_repo=feature_stats_repo,  # 기존 feature_stats용 Repository
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

    # Repository 패턴 적용된 서비스들
    forecast_service = ForecastService(elderly_repo=elderly_history_repo)
    elderly_service = ElderlyService(SqlAlchemyElderlyHistoryRepository())
    region_risk_service = RegionRiskService(
        prediction_service=prediction_service,
        elderly_stats_repo=elderly_stats_repo,
    )

    # --- 서비스 컨테이너 등록 ---
    services = {
        # Repos
        "region_repo": region_repo,
        "feature_stats_repo": feature_stats_repo,  # 기존
        "elderly_history_repo": elderly_history_repo,  # 신규
        "elderly_stats_repo": elderly_stats_repo,  # 신규
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
        "region_risk_service": region_risk_service,
    }

    app.config["services"] = services
    return services
