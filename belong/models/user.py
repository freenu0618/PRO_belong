# belong/models/user.py

from belong.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Sequence

class User(db.Model):
    """
    간단한 회원 정보 테이블
    - USER 테이블에 매핑
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"
