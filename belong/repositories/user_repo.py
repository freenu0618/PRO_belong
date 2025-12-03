# repositories/user_repo.py
from typing import Optional
from belong.extensions import db
from belong.models.user import User

class UserRepository:
    def get_by_username(self, username: str) -> Optional[User]:
        return User.query.filter_by(username=username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return User.query.filter_by(email=email).first()

    def create_user(self, username: str, email: str, raw_password: str) -> User:
        user = User(username=username, email=email)
        user.set_password(raw_password)  # 모델 메서드 사용
        db.session.add(user)
        db.session.commit()
        return user
