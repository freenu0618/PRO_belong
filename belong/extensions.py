import logging
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("belong")
logger.setLevel(logging.INFO)
db = SQLAlchemy()