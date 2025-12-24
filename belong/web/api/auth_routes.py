# belong/web/api/auth_routes.py
from flask import request, g
from . import api_bp

from belong.services.auth_service import AuthService
from .jwt_utils import create_access_token, jwt_required
from .response_utils import success_response, bad_request, unauthorized


def get_auth_service():
    """Flask application context 내에서 AuthService 가져오기"""
    if not hasattr(g, 'auth_service'):
        g.auth_service = AuthService()
    return g.auth_service


@api_bp.post("/auth/signup")
def api_signup():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return bad_request("아이디, 이메일, 비밀번호는 모두 필수입니다.")

    auth_service = get_auth_service()
    ok, msg, user = auth_service.signup(username, email, password)
    if not ok:
        return bad_request(msg)

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    })

    return success_response(
        data={
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        },
        message=msg,
        status_code=201
    )


@api_bp.post("/auth/login")
def api_login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return bad_request("아이디와 비밀번호를 입력해주세요.")

    auth_service = get_auth_service()
    ok, msg, user = auth_service.login(username, password)
    if not ok:
        return unauthorized(msg)

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    })

    return success_response(
        data={
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        },
        message=msg
    )


@api_bp.get("/auth/me")
@jwt_required
def api_me():
    payload = getattr(g, "jwt_payload", {}) or {}
    return success_response(
        data={
            "user": {
                "id": payload.get("sub"),
                "username": payload.get("username"),
                "email": payload.get("email"),
            }
        }
    )


@api_bp.post("/auth/logout")
def api_logout():
    # JWT는 서버 세션이 아니라 토큰이므로,
    # 기본 로그아웃은 프론트에서 토큰 삭제로 처리.
    return success_response(
        message="로그아웃 되었습니다."
    )
