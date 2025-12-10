from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

logger = logging.getLogger("belong")
logger.setLevel(logging.INFO)

# SQLAlchemy ORM
db = SQLAlchemy()

# Flask-Migrate (Alembic 래퍼)
migrate = Migrate()
