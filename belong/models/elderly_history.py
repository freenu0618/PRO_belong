# belong/models/elderly_history.py

from sqlalchemy import func, UniqueConstraint
from belong.extensions import db

class ElderlyHistory(db.Model):
    __tablename__ = "ELDERLY_HISTORY"

    id = db.Column(
        db.Integer,
        db.Sequence("ELDERLY_HISTORY_SEQ"),
        primary_key=True,
    )
    region_id = db.Column(
        db.Integer,
        db.ForeignKey("REGION.id", name="FK_ELD_HIST_REGION"),
        nullable=False,
    )
    year = db.Column(db.Integer, nullable=False)

    elderly_population = db.Column(db.Integer)
    alone_elderly_population = db.Column(db.Integer)

    is_forecast = db.Column(
        db.String(1),
        nullable=False,
        server_default="N",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at = db.Column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "year",
            "is_forecast",
            name="UQ_ELD_HIST_REG_YR_FC",  # 30자 이하
        ),
    )

    region = db.relationship("Region", back_populates="elderly_histories")


    def __repr__(self):
        return (
            f"<ElderlyHistory(region_id={self.region_id}, "
            f"year={self.year}, is_forecast={self.is_forecast})>"
        )
