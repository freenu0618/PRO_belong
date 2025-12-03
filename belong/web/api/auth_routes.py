# web/api/auth_routes.py
from flask import jsonify, request
from . import api_bp

from belong.services.auth_service import AuthService

auth_service = AuthService()  # 전역으로 한 번 생성


@api_bp.post("/auth/signup")
def api_signup():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # (필수값 체크는 route에서 해도 OK)
    if not username or not email or not password:
        return jsonify({
            "status": "error",
            "message": "아이디, 이메일, 비밀번호는 모두 필수입니다."
        }), 400

    ok, msg, user = auth_service.signup(username, email, password)

    if not ok:
        # 중복, 비밀번호 규칙 위반 등
        return jsonify({"status": "error", "message": msg}), 400

    return jsonify({
        "status": "success",
        "message": msg,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
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

    return jsonify({
        "status": "success",
        "message": msg,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }), 200

@api_bp.post("/auth/logout")
def api_logout():
    """
    POST /api/auth/logout
    - 서버 세션을 안 쓰고 있으니, 그냥 성공 응답만 주면 됨.
    - 프론트에서는 localStorage.removeItem('belong_user') 같은 식으로 처리.
    """
    return jsonify({
        "status": "success",
        "message": "로그아웃 되었습니다."
    }), 200
