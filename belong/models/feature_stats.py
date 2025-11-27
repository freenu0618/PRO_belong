# belong/models/feature_stats.py

from belong.extensions import db
from sqlalchemy import UniqueConstraint


class ElderlyStats(db.Model):
    """
    ELDERLY_STATS 테이블 ORM 모델.

    - REGION_ID + YEAR 로 한 구의 한 해 데이터를 표현
    - merged_dataset.csv 의 feature 컬럼을 거의 그대로 매핑
    """

    __tablename__ = "ELDERLY_STATS"

    # 기본 키
    id = db.Column("id", db.Integer, primary_key=True)

    # FK: REGION.id
    region_id = db.Column(
        "region_id",
        db.Integer,
        db.ForeignKey("REGION.id"),
        nullable=False,
    )

    # 연도
    year = db.Column("year", db.Integer, nullable=False)

    # ---------- 주거 형태 ----------
    single_house_total = db.Column("single_house_total", db.Integer)
    apartment_total = db.Column("apartment_total", db.Integer)
    row_house_total = db.Column("row_house_total", db.Integer)
    multi_house_total = db.Column("multi_house_total", db.Integer)
    non_residential_housing_total = db.Column("non_residential_housing_total", db.Integer)

    # ---------- 타깃(고독사) 및 지표 ----------
    target_value = db.Column("target_value", db.Integer)
    aging_index = db.Column("aging_index", db.Float)

    # ---------- 인구 관련 ----------
    population_total = db.Column("population_total", db.Integer)
    population_male = db.Column("population_male", db.Integer)
    population_female = db.Column("population_female", db.Integer)
    population_change_count = db.Column("population_change_count", db.Integer)
    population_growth_ratio = db.Column("population_growth_ratio", db.Float)

    single_household_ratio = db.Column("single_household_ratio", db.Float)

    under_20 = db.Column("under_20", db.Integer)
    age_65_over = db.Column("age_65_over", db.Integer)
    age_0_14 = db.Column("age_0_14", db.Integer)

    cpi_index = db.Column("cpi_index", db.Float)

    # ---------- 저소득 노인 비율 ----------
    low_income_elderly_65_79_ratio = db.Column("LOW_INC_65_79_RATIO", db.Float)
    low_income_elderly_80_over_ratio = db.Column("LOW_INC_80_PLUS_RATIO", db.Float)

    # ---------- 기초연금/독거 관련 ----------
    basic_pension_recipient_count = db.Column("basic_pension_recipient_count", db.Integer)
    basic_pension_recipient_ratio = db.Column("basic_pension_recipient_ratio", db.Float)

    alone_household_count = db.Column("alone_household_count", db.Integer)
    elderly_population = db.Column("elderly_population", db.Integer, nullable=True)

    # ---------- 생성/수정 일시 ----------
    created_at = db.Column(
        "created_at",
        db.DateTime,
        server_default=db.func.current_timestamp(),
    )
    updated_at = db.Column(
        "updated_at",
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Region 관계 (Region.elderly_stats 와 양방향)
    region = db.relationship(
        "Region",
        back_populates="elderly_stats",
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint("region_id", "year", name="uq_elderly_stats_region_year"),
    )

    def __repr__(self) -> str:
        return (
            f"<ElderlyStats id={self.id} region_id={self.region_id} "
            f"year={self.year} elderly_population={self.elderly_population}>"
        )
