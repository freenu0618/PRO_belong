"""
API 응답 표준화 유틸리티
모든 API 응답은 이 모듈을 통해 생성되어야 합니다.
"""

from flask import jsonify
from typing import Any, Optional, Dict


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> tuple:
    """
    성공 응답 생성
    
    Args:
        data: 응답 데이터
        message: 성공 메시지 (선택)
        status_code: HTTP 상태 코드 (기본: 200)
    
    Returns:
        (response, status_code) 튜플
    
    Example:
        return success_response({"user": user_dict}, "로그인 성공")
    """
    response = {"ok": True}
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    return jsonify(response), status_code


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict] = None
) -> tuple:
    """
    에러 응답 생성
    
    Args:
        message: 에러 메시지
        status_code: HTTP 상태 코드 (기본: 400)
        error_code: 에러 코드 (선택)
        details: 추가 상세 정보 (선택)
    
    Returns:
        (response, status_code) 튜플
    
    Example:
        return error_response("사용자를 찾을 수 없습니다", 404, "USER_NOT_FOUND")
    """
    response = {
        "ok": False,
        "error": {
            "message": message
        }
    }
    
    if error_code:
        response["error"]["code"] = error_code
    
    if details:
        response["error"]["details"] = details
    
    return jsonify(response), status_code


# 자주 사용하는 에러 응답 단축 함수들
def bad_request(message: str, details: Optional[Dict] = None):
    """400 Bad Request"""
    return error_response(message, 400, "BAD_REQUEST", details)


def unauthorized(message: str = "인증이 필요합니다"):
    """401 Unauthorized"""
    return error_response(message, 401, "UNAUTHORIZED")


def forbidden(message: str = "접근 권한이 없습니다"):
    """403 Forbidden"""
    return error_response(message, 403, "FORBIDDEN")


def not_found(message: str = "리소스를 찾을 수 없습니다"):
    """404 Not Found"""
    return error_response(message, 404, "NOT_FOUND")


def server_error(message: str = "서버 오류가 발생했습니다"):
    """500 Internal Server Error"""
    return error_response(message, 500, "INTERNAL_SERVER_ERROR")
