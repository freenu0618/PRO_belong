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
    # SECURITY: SECRET_KEY and JWT_SECRET are REQUIRED in environment variables
    # These keys are critical for session management and JWT token security
    SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
    JWT_SECRET = (os.getenv("JWT_SECRET") or "").strip()

    # Validate that secrets are properly set (no fallback allowed)
    if not SECRET_KEY or SECRET_KEY == "dev-secret-change-me":
        raise RuntimeError(
            "❌ SECURITY ERROR: SECRET_KEY must be set in environment variables (.env file).\n"
            "   Generate a secure key: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

    if not JWT_SECRET or JWT_SECRET == "dev-secret-change-me":
        raise RuntimeError(
            "❌ SECURITY ERROR: JWT_SECRET must be set in environment variables (.env file).\n"
            "   Generate a secure key: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

    # Ensure both keys are set (jwt_utils may reference either)
    if not JWT_SECRET:
        JWT_SECRET = SECRET_KEY
    if not SECRET_KEY:
        SECRET_KEY = JWT_SECRET

    JWT_ALG = (os.getenv("JWT_ALG") or "HS256").strip()
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES") or "60")

    # -----------------------------
    # Security (Ngrok etc)
    # -----------------------------
    # CSRF 방어 설정 (Ngrok 도메인 허용)
    # [Demo Fix] RunPod 동적 IP 접속 시 CSRF 에러 방지를 위해 비활성화
    WTF_CSRF_ENABLED = True 
    WTF_CSRF_TRUSTED_ORIGINS = [
        "https://*.ngrok-free.dev", 
        "https://*.ngrok.io",
        "https://*.runpod.net",
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ]

    # -----------------------------
    # DB (PostgreSQL)
    # -----------------------------
    # DATABASE_URI가 있으면(Postgres) 사용, 없으면 로컬 SQLite 사용 (개발 편의성)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", os.getenv("DATABASE_URL")) or "sqlite:///local_dev.db"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------
    # AI Service
    # -----------------------------
    # -----------------------------
    # AI Service (RunPod & Ollama)
    # -----------------------------
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    # RunPod Configuration (Pod Direct Connection)
    # Direct TCP Address (Bypassing RunPod Proxy for stability)
    RUNPOD_ENDPOINT_URL = os.getenv("RUNPOD_ENDPOINT_URL", "http://127.0.0.1:8000/generate")
    RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")


    # -----------------------------
    # ML
    # -----------------------------
    MODEL_PATH = os.getenv("MODEL_PATH")
