from belong.extensions import db

class ElderlyHistory(db.Model):
    """
    독거노인/고령 인구 연도별 히스토리 테이블 매핑

    ELDERLY_HISTORY
    - REGION_NAME (PK)
    - YEAR        (PK)
    - ELDERLY_POP
    """

    __tablename__ = "ELDERLY_HISTORY"

    region_name = db.Column(db.String(50), primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    elderly_pop = db.Column(db.Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<ElderlyHistory region={self.region_name} year={self.year} pop={self.elderly_pop}>"