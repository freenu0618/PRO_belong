from belong.extensions import db
from datetime import datetime


class PredictionResult(db.Model):
    __tablename__ = "PREDICTION_RESULT"

    id = db.Column(db.Integer, primary_key=True)
    region_name = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    prediction_value = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(30), nullable=False, default="rule_based")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("region_name", "year", name="uq_prediction_region_year"),
    )
