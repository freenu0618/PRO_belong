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
