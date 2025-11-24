import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MODEL_PATH = os.getenv("MODEL_PATH")
    ENV = os.getenv("APP_ENV", "development")
