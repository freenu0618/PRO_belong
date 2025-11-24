from flask import jsonify, request # 딕셔너리를 json 문자열로 변환, response 객체로 감싸고 application/json 헤더도 자동 설정
from . import api_bp
from belong.services.population_service import PopulationService
from belong.services.forecast_service import ForecastService
from belong.services.correlation_service import CorrelationService

population_service = PopulationService()
forecast_service = ForecastService()
correlation_service = CorrelationService()

# TODO: 이후 DB/ML 연동 대신하는 Mock 데이터
MOCK_DATA = {
    "강남구": {
        "history": [
            {"year": 2019, "value": 12000},
            {"year": 2020, "value": 12400},
            {"year": 2021, "value": 13000},
            {"year": 2022, "value": 13800},
        ],
        "forecast": [
            {"year": 2023, "value": 14500},
            {"year": 2024, "value": 15000}
        ]
    },
    "종로구": {
        "history": [
            {"year": 2019, "value": 12400},
            {"year": 2020, "value": 12600},
            {"year": 2021, "value": 12850},
            {"year": 2022, "value": 13120},
        ],
        "forecast": [
            {"year": 2023, "value": 13700},
            {"year": 2024, "value": 14300}
        ]
    }
}

@api_bp.get("/predict")
def predict():
    region = request.args.get("region")

    if not region:
        return jsonify({"status": "error", "message": "region parameter is required"}), 400

    if region not in MOCK_DATA:
        return jsonify({"status": "error", "message": "region not found"}), 404

    result = {
        "status": "success",
        "data": {
            "region": region,
            "history": MOCK_DATA[region]["history"],
            "forecast": MOCK_DATA[region]["forecast"]
        }
    }

    return jsonify(result), 200


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