# belong/web/api/auth_routes.py
from flask import jsonify, request, g
from . import api_bp

from belong.services.auth_service import AuthService
from .jwt_utils import create_access_token, jwt_required

auth_service = AuthService()


@api_bp.post("/auth/signup")
def api_signup():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({
            "status": "error",
            "message": "아이디, 이메일, 비밀번호는 모두 필수입니다."
        }), 400

    ok, msg, user = auth_service.signup(username, email, password)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 400

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    })

    return jsonify({
        "status": "success",
        "message": msg,
        "data": {
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }
    }), 201


@api_bp.post("/auth/login")
def api_login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "아이디와 비밀번호를 입력해주세요."
        }), 400

    ok, msg, user = auth_service.login(username, password)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 401

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    })

    return jsonify({
        "status": "success",
        "message": msg,
        "data": {
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }
    }), 200


@api_bp.get("/auth/me")
@jwt_required
def api_me():
    payload = getattr(g, "jwt_payload", {}) or {}
    return jsonify({
        "status": "success",
        "data": {
            "user": {
                "id": payload.get("sub"),
                "username": payload.get("username"),
                "email": payload.get("email"),
            }
        }
    }), 200


@api_bp.post("/auth/logout")
def api_logout():
    # JWT는 서버 세션이 아니라 토큰이므로,
    # 기본 로그아웃은 프론트에서 토큰 삭제로 처리.
    return jsonify({
        "status": "success",
        "message": "로그아웃 되었습니다."
    }), 200
