# config.py
import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()

BASE_DIR = os.path.dirname(__file__)


class Config:
    # -----------------------------
    # App / Environment
    # -----------------------------
    ENV = os.getenv("APP_ENV", "development")
    DEBUG = (ENV == "development")

    # -----------------------------
    # ✅ JWT / Flask Secret (가장 중요)
    # -----------------------------
    # 1순위: JWT_SECRET (권장)
    # 2순위: SECRET_KEY (Flask 기본)
    # 개발환경에서도 None/빈값이면 토큰 검증이 깨지므로 fallback을 둔다.
    SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
    JWT_SECRET = (os.getenv("JWT_SECRET") or "").strip()

    if not SECRET_KEY and not JWT_SECRET:
        # 개발용 fallback (운영에서는 반드시 .env로 주입)
        SECRET_KEY = "dev-secret-change-me"
        JWT_SECRET = "dev-secret-change-me"

    # jwt_utils가 SECRET_KEY/JWT_SECRET 둘 중 무엇을 보더라도 동일하게 동작하도록 통일
    if not JWT_SECRET:
        JWT_SECRET = SECRET_KEY
    if not SECRET_KEY:
        SECRET_KEY = JWT_SECRET

    JWT_ALG = (os.getenv("JWT_ALG") or "HS256").strip()
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES") or "60")

    # -----------------------------
    # DB (Oracle)
    # -----------------------------
    ORACLE_USER = os.getenv("ORACLE_USER", "scott")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "tiger")
    ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost:1521/xe")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URI",
        f"oracle+cx_oracle://{ORACLE_USER}:{ORACLE_PASSWORD}@{ORACLE_DSN}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------
    # ML
    # -----------------------------
    MODEL_PATH = os.getenv("MODEL_PATH")
