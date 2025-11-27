from belong.extensions import db
from datetime import datetime
from sqlalchemy import Sequence


class PredictionResult(db.Model):
    __tablename__ = "PREDICTION_RESULT"

    id = db.Column(
        db.Integer,
        Sequence("PREDICTION_RESULT_ID_SEQ"),  # 🔥 SEQUENCE 이름
        primary_key=True,
    )
    region_name = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    prediction_value = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(30), nullable=False, default="rule_based")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("region_name", "year", name="uq_prediction_region_year"),
    )
