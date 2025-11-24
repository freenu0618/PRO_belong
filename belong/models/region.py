# belong/models/region.py

from belong.extensions import db


class Region(db.Model):
    """
    서울 25개 구(그리고 이후 확장될 수 있는 지역)를 나타내는 마스터 테이블.

    한 행 = 1개 구
    예: 강남구, 종로구, 동작구 ...
    """

    __tablename__ = "REGION"

    id = db.Column(db.Integer, primary_key=True)  # ID (PK)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 구 이름 (예: 강남구)
    code = db.Column(db.String(10), nullable=True)  # 행정 코드 (선택)

    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # 나중에 relationship로 ElderlyStats와 연결할 예정
    elderly_stats = db.relationship(
        "ElderlyStats",
        back_populates="region",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Region id={self.id} name={self.name}>"
