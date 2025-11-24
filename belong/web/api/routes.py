from flask import jsonify, request # 딕셔너리를 json 문자열로 변환, response 객체로 감싸고 application/json 헤더도 자동 설정
from . import api_bp
from belong.services.population_service import PopulationService
from belong.services.forecast_service import ForecastService
from belong.services.correlation_service import CorrelationService
from ...services.prediction_service import PredictionService


population_service = PopulationService()
forecast_service = ForecastService()
correlation_service = CorrelationService()

service = PredictionService()

@api_bp.get("/predict")
def predict():


    region = request.args.get("region")
    years = request.args.get("years", default=2, type=int)

    # 1) 필수값 검증
    if not region:
        return jsonify({
            "status": "error",
            "message": "Missing required parameter: region"
        }), 400

    # 2) 서비스 호출
    result = forecast_service.forecast_region(region, n_years=years)

    # 3) 모델 없거나 예측 실패
    if result is None or result.get("forecast") is None:
        return jsonify({
            "status": "error",
            "message": f"No forecast model available for region '{region}'"
        }), 404

    # 4) 정상 응답
    return jsonify({
        "status": "success",
        "data": result
    }), 200



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