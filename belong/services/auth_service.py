# services/auth_service.py
from typing import Optional, Tuple
from belong.repositories.user_repo import UserRepository
from belong.models.user import User

class AuthService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    def signup(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        # 중복 체크
        if self.user_repo.get_by_username(username):
            return False, "이미 사용 중인 아이디입니다.", None
        if self.user_repo.get_by_email(email):
            return False, "이미 가입된 이메일입니다.", None

        if len(password) < 6:
            return False, "비밀번호는 6자 이상이어야 합니다.", None

        user = self.user_repo.create_user(username, email, password)
        return True, "회원가입이 완료되었습니다.", user

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        user = self.user_repo.get_by_username(username)
        if user is None:
            return False, "아이디 또는 비밀번호가 올바르지 않습니다.", None

        if not user.check_password(password):
            return False, "아이디 또는 비밀번호가 올바르지 않습니다.", None

        return True, "로그인 성공", user
