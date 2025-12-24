# belong/app.py
from pathlib import Path

from flask import Flask

from belong.web.api import api_bp  # /api/v1/... REST API 엔드포인트 모음
from belong.web.main import web_bp  # 화면 렌더링용 엔드포인트 모음

from belong.extensions import db, migrate, logger
from config import Config
from belong.services.registry import register_services
from belong.ml.region_weights import load_region_weights

# PostgreSQL 사용 (Oracle 제거됨)

"""
api_bp → /api/v1/... 같은 REST API 엔드포인트 모음
web_bp → /, /dashboard 같은 화면 렌더링용 엔드포인트 모음
"""

# 현재 파일(app.py)이 있는 디렉터리 (= belong 폴더)
BASE_DIR = Path(__file__).resolve().parent


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
    3) 확장(extenstions) 초기화 (db.init_app, migrate.init_app)
    4) 서비스 등록 (register_services)
    5) Blueprint 등록
    6) region_feature_weights.csv 로드 (룰베이스 가중치)
    """
    app = Flask(__name__)

    # 1) 설정 로드
    app.config.from_object(Config)

    # 2) 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)

    # 3) 서비스 등록 (레포/서비스를 생성하고 app.config["services"]에 넣어둠)
    register_services(app)

    # 4) 블루프린트 등록
    safe_register(app, api_bp)
    safe_register(app, web_bp)

    # 5) region_feature_weights.csv 로드
    weights_path = BASE_DIR / "ml" / "region_feature_weights.csv"
    try:
        load_region_weights(weights_path)
        logger.info(f"[app] Loaded region weights from {weights_path}")
    except FileNotFoundError as e:
        # 개발 단계에서 파일이 없을 수 있으므로, 앱은 살려두고 경고만 출력
        logger.warning(f"[app] Could not load region weights: {e}")

    logger.info("Flask app created with PostgreSQL + SQLAlchemy configuration.")
    return app


if __name__ == "__main__":
    # python -m belong.app 또는 python app.py 로 직접 실행할 때 진입점
    app = create_app()
    app.run(debug=True)
