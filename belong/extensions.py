from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

logger = logging.getLogger("belong")
logger.setLevel(logging.INFO)

# Add console handler for log output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# SQLAlchemy ORM
db = SQLAlchemy()

# Flask-Migrate (Alembic 래퍼)
migrate = Migrate()
