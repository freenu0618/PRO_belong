from flask import jsonify # 딕셔너리를 json 문자열로 변환, response 객체로 감싸고 application/json 헤더도 자동 설정
from . import api_bp
from belong.services.population_service import PopulationService
from belong.services.forecast_service import ForecastService
from belong.services.correlation_service import CorrelationService

population_service = PopulationService()
forecast_service = ForecastService()
correlation_service = CorrelationService()

@api_bp.route('/health') # 실행흐름 : 브라우저 요청 → /api/v1/health → api_bp.route 등록된 health 함수 실행
def health(): # /health 요청을 처리하는 뷰 함수.
    return jsonify({"status": "ok"})

@api_bp.route("/elderly/population")
def elderly_population():
    data = population_service.get_summary()
    return jsonify({"status": "success", "data": data})

@api_bp.route("/elderly/forecast/<region>")
def elderly_forecast(region):
    data = forecast_service.forecast_region(region)
    if data is None:
        return jsonify({"status": "error", "message": "Region not found"}), 404
    return jsonify({"status": "success", "data": data})

@api_bp.route("/elderly/correlation")
def elderly_correlation():
    data = correlation_service.compute()
    return jsonify({"status": "success", "data": data})
