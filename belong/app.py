from flask import Flask

from belong.web.api import api_bp  # /api/v1/... REST API 엔드포인트 모음
from belong.web.main import web_bp  # 화면 렌더링용 엔드포인트 모음

from belong.extensions import db, migrate, logger
from config import Config
from belong.repositories.feature_stats_repo import ElderlyStatsRepository
from belong.repositories.region_repo import RegionRepository
from belong.services.feature_stats_service import FeatureStatsService

"""
api_bp → /api/v1/... 같은 REST API 엔드포인트 모음
web_bp → /, /dashboard 같은 화면 렌더링용 엔드포인트 모음
"""


def safe_register(app: Flask, bp):
    """
    같은 Blueprint가 중복 등록되는 걸 방지하기 위한 유틸 함수.
    (나중에 create_app을 여러 번 호출하는 경우를 대비해서.)
    """
    if bp.name not in app.blueprints:
        app.register_blueprint(bp)
    else:
        print(f"[WARN] Blueprint '{bp.name}' already registered. Skipping.")


def create_app() -> Flask:
    """
    Flask 애플리케이션 팩토리 함수.

    1) Flask 인스턴스 생성
    2) Config 적용 (Oracle/SQLAlchemy 설정 포함)
    3) 확장(extenstions) 초기화 (db.init_app)
    4) Blueprint 등록
    """
    app = Flask(__name__)

    # 1) 설정 로드 (config.Config 클래스 사용)
    app.config.from_object(Config)

    # 2) 확장 초기화 (SQLAlchemy ORM 연결)
    db.init_app(app)

    # 3) 마이그레이션 초기화
    migrate.init_app(app, db)

    # --- Repository 인스턴스 생성 ---
    elderly_stats_repo = ElderlyStatsRepository()
    region_repo = RegionRepository()

    # --- Service 인스턴스 생성 ---
    feature_stats_service = FeatureStatsService(
        elderly_stats_repo=elderly_stats_repo,
        region_repo=region_repo,
    )

    # --- app.config["services"]에 등록 ---
    app.config.setdefault("services", {})
    app.config["services"].update(
        {
            "elderly_stats_repo": elderly_stats_repo,
            "region_repo": region_repo,
            "feature_stats_service": feature_stats_service,
        }
    )


    # 4) 블루프린트 등록
    #    - API: /api/v1/...
    #    - WEB: 화면 렌더링용
    safe_register(app, api_bp)
    safe_register(app, web_bp)

    logger.info("Flask app created with Oracle + SQLAlchemy configuration.")

    return app


if __name__ == "__main__":
    # python app.py 로 직접 실행할 때 진입점
    app = create_app()
    app.run(debug=True)
