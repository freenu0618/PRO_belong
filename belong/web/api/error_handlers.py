"""
API 에러 핸들러
Flask Blueprint에서 발생하는 모든 에러를 중앙에서 처리
"""

from flask import Blueprint
from werkzeug.exceptions import HTTPException
from belong.web.api.response_utils import error_response, server_error
from belong.extensions import logger


def register_error_handlers(bp: Blueprint):
    """
    Blueprint에 에러 핸들러 등록
    
    Args:
        bp: Flask Blueprint
    """
    
    @bp.errorhandler(400)
    def handle_bad_request(e):
        """400 Bad Request"""
        logger.warning(f"Bad Request: {e}")
        return error_response(
            message=str(e.description) if hasattr(e, 'description') else "잘못된 요청입니다",
            status_code=400,
            error_code="BAD_REQUEST"
        )
    
    @bp.errorhandler(401)
    def handle_unauthorized(e):
        """401 Unauthorized"""
        logger.warning(f"Unauthorized: {e}")
        return error_response(
            message="인증이 필요합니다",
            status_code=401,
            error_code="UNAUTHORIZED"
        )
    
    @bp.errorhandler(403)
    def handle_forbidden(e):
        """403 Forbidden"""
        logger.warning(f"Forbidden: {e}")
        return error_response(
            message="접근 권한이 없습니다",
            status_code=403,
            error_code="FORBIDDEN"
        )
    
    @bp.errorhandler(404)
    def handle_not_found(e):
        """404 Not Found"""
        logger.warning(f"Not Found: {e}")
        return error_response(
            message="리소스를 찾을 수 없습니다",
            status_code=404,
            error_code="NOT_FOUND"
        )
    
    @bp.errorhandler(500)
    def handle_server_error(e):
        """500 Internal Server Error"""
        logger.error(f"Server Error: {e}", exc_info=True)
        return server_error("서버 오류가 발생했습니다")
    
    @bp.errorhandler(Exception)
    def handle_unexpected_error(e):
        """모든 예외 처리"""
        logger.error(f"Unexpected Error: {e}", exc_info=True)
        
        # HTTP 예외는 그대로 전달
        if isinstance(e, HTTPException):
            return error_response(
                message=str(e.description),
                status_code=e.code,
                error_code=e.name.upper().replace(' ', '_')
            )
        
        # 그 외 예외는 500으로 처리
        return server_error(f"예기치 않은 오류: {str(e)}")
