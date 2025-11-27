from belong.extensions import db
from belong.models.region import Region

# class ElderlyHistory(db.Model):
#     """
#     독거노인/고령 인구 연도별 히스토리 테이블 매핑
#
#     ELDERLY_HISTORY
#     - REGION_NAME (PK)
#     - YEAR        (PK)
#     - ELDERLY_POP
#     """
#
#     __tablename__ = "ELDERLY_HISTORY"
#
#     region_name = db.Column(db.String(50), primary_key=True)
#     year = db.Column(db.Integer, primary_key=True)
#     elderly_pop = db.Column(db.Integer, nullable=False)
#
#     def __repr__(self) -> str:
#         return f"<ElderlyHistory region={self.region_name} year={self.year} pop={self.elderly_pop}>"
#

# class ElderlyStats(db.Model):
#     """
#     구 × 연도별 통계를 담는 테이블.

#     - 하나의 행 = (region, year)에 대한 모든 지표
#     - merged_dataset.csv 한 줄이 여기에 매핑된다고 보면 된다.
#     """

#     __tablename__ = "ELDERLY_STATS"

#     id = db.Column(db.Integer, primary_key=True)

#     # REGION FK
#     region_id = db.Column(db.Integer, db.ForeignKey("REGION.id"), nullable=False)
#     year = db.Column(db.Integer, nullable=False)

#     # ===== CSV 매핑 컬럼 (one-hot 구 컬럼 25개는 제외) =====

#     # 주거타입 관련
#     single_house_total = db.Column(db.Integer)          # single_house_total
#     apartment_total = db.Column(db.Integer)             # apartment_total
#     row_house_total = db.Column(db.Integer)             # row_house_total
#     multi_house_total = db.Column(db.Integer)           # multi_house_total
#     non_residential_housing_total = db.Column(db.Integer)  # non_residential_housing_total

#     # 타겟/인구 구조/경제 관련
#     target_value = db.Column(db.Integer)                # target_value (고독사 건수 등)
#     aging_index = db.Column(db.Float)                   # aging_index
#     population_total = db.Column(db.Integer)            # population_total
#     population_male = db.Column(db.Integer)             # population_male
#     population_female = db.Column(db.Integer)           # population_female
#     population_change_count = db.Column(db.Integer)     # population_change_count
#     population_growth_ratio = db.Column(db.Float)       # population_growth_ratio
#     single_household_ratio = db.Column(db.Float)        # single_household_ratio

#     under_20 = db.Column(db.Integer)                    # under_20
#     age_65_over = db.Column(db.Integer)                 # age_65_over
#     age_0_14 = db.Column(db.Integer)                    # age_0_14
#     cpi_index = db.Column(db.Float)                     # cpi_index

#     low_income_elderly_65_79_ratio = db.Column(
#         "LOW_INC_65_79_RATIO",
#         db.Float,
#     )    # low_income_elderly_65_79_ratio
#     low_income_elderly_80_over_ratio = db.Column(
#         "LOW_INC_80_PLUS_RATIO",
#         db.Float,
#     )  # low_income_elderly_80_over_ratio

#     basic_pension_recipient_count = db.Column(db.Integer)   # basic_pension_recipient_count
#     basic_pension_recipient_ratio = db.Column(db.Float)     # basic_pension_recipient_ratio

#     alone_household_count = db.Column(db.Integer)       # alone_household_count (1인가구 수)
#     elderly_population = db.Column(db.Integer)          # elderly_population (우리가 말하는 독거노인 인구)

#     created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
#     updated_at = db.Column(
#         db.DateTime,
#         server_default=db.func.current_timestamp(),
#         onupdate=db.func.current_timestamp(),
#     )

#     # Region과의 관계
#     region = db.relationship(
#         Region,
#         back_populates="elderly_stats",
#         lazy="joined",
#     )

#     __table_args__ = (
#         db.UniqueConstraint("region_id", "year", name="uq_elderly_stats_region_year"),
#     )

#     def __repr__(self) -> str:
#         return f"<ElderlyStats region_id={self.region_id} year={self.year} elderly={self.elderly_population}>"