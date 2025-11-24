import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
BASE_DIR = os.path.dirname(__file__)
print("BASE_DIR:",BASE_DIR)
load_dotenv()

class Config:
    MODEL_PATH = os.getenv("MODEL_PATH")
    ENV = os.getenv("APP_ENV", "development")
    ORACLE_USER = os.getenv("ORACLE_USER", "scott")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "tiger")
    ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost:1521/xe")
    SQLALCHEMY_DATABASE_URI = (
        f"oracle+cx_oracle://{ORACLE_USER}:{ORACLE_PASSWORD}@{ORACLE_DSN}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
