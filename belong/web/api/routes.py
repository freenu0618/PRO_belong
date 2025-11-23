from flask import jsonify # 딕셔너리를 json 문자열로 변환, response 객체로 감싸고 application/json 헤더도 자동 설정
from . import api_bp

@api_bp.route('/health') # 실행흐름 : 브라우저 요청 → /api/v1/health → api_bp.route 등록된 health 함수 실행
def health(): # /health 요청을 처리하는 뷰 함수.
    return jsonify({"status": "ok"})