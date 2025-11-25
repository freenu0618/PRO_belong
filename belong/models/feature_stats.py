# belong/models/elderly_stats.py
from belong.extensions import db
from sqlalchemy import UniqueConstraint


class ElderlyStats(db.Model):
    __tablename__ = "ELDERLY_STATS"

    id = db.Column("ID", db.Integer, primary_key=True)
    region_id = db.Column(
        "REGION_ID",
        db.Integer,
        db.ForeignKey("REGION.id"),   # 🔴 여기만 이렇게 바꿔주면 됨
        nullable=False,
    )
    year = db.Column("YEAR", db.Integer, nullable=False)
    elderly_population = db.Column("ELDERLY_POPULATION", db.Integer, nullable=False)

    region = db.relationship(
        "Region",
        back_populates="elderly_stats",
        lazy="joined",
    )

    __table_args__ = (
        # 한 구(region_id)에서 같은 year가 중복되지 않도록 제약 (선택사항이지만 강력 추천)
        UniqueConstraint("REGION_ID", "YEAR", name="uq_elderly_stats_region_year"),
    )

    def __repr__(self) -> str:
        return (f"<ElderlyStats id={self.id} region_id={self.region_id} "
                f"year={self.year} elderly_population={self.elderly_population}>")
