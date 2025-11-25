from flask import jsonify, request, current_app  # 딕셔너리를 JSON 응답으로 감싸주는 유틸
from . import api_bp
from belong.services.population_service import PopulationService
from belong.services.forecast_service import ForecastService
from belong.services.correlation_service import CorrelationService
from belong.repositories.elderly_repo import SqlAlchemyElderlyHistoryRepository

# Service 인스턴스들은 지금은 간단히 전역으로 올려도 괜찮음
population_service = PopulationService()
# Oracle 연결을 우선 시도하고, 실패하면 InMemory로 fallback
repo = SqlAlchemyElderlyHistoryRepository()
forecast_service = ForecastService(repo=repo)

correlation_service = CorrelationService()


@api_bp.get("/predict")
def predict():
    """
    독거노인 인구 예측 API (v0.2)

    쿼리 파라미터:
      - region: 필수, '강남구' 등
      - horizon: 선택, 'short' 또는 'long' (기본: 'short')
      - years: 선택, 정수. 주어지면 horizon보다 우선.

    예:
      GET /api/v1/predict?region=강남구                -> short(3년) 예측
      GET /api/v1/predict?region=강남구&horizon=long  -> long(10년) 예측
      GET /api/v1/predict?region=강남구&years=5       -> 5년 예측
    """
    region = request.args.get("region")
    horizon = request.args.get("horizon", "short")
    years_param = request.args.get("years", type=int)

    # 1) region 필수 검증
    if not region:
        return jsonify({
            "status": "error",
            "message": "Missing required parameter: region"
        }), 400

    # 2) horizon / years 해석
    valid_horizons = ("short", "long")
    if years_param is not None and years_param <= 0:
        return jsonify({
            "status": "error",
            "message": "years must be a positive integer"
        }), 400

    if years_param is not None:
        n_years = years_param
    else:
        if horizon not in valid_horizons:
            return jsonify({
                "status": "error",
                "message": "horizon must be 'short' or 'long' (or provide years param)"
            }), 400

        if horizon == "short":
            n_years = 3
        else:  # horizon == "long"
            n_years = 10

    # 3) 서비스 호출
    result = forecast_service.forecast_region(region=region,
                                              n_years=n_years,
                                              horizon=horizon)

    # 4) region 자체가 없는 경우
    if result is None or result.get("history") is None:
        return jsonify({
            "status": "error",
            "message": f"Region '{region}' not found"
        }), 404

    # 5) 정상 응답
    return jsonify({
        "status": "success",
        "data": result,
        "meta": {
            "horizon": horizon,
            "years": n_years
        }
    }), 200


@api_bp.get("/health")
def health():
    """
    서비스 헬스 체크용 엔드포인트

    - 브라우저나 모니터링 도구에서 /api/v1/health 를 호출해서
      서버가 살아있는지 확인하는 목적.
    """
    return jsonify({"status": "ok"})


@api_bp.get("/elderly/population")
def elderly_population():
    """
    독거노인 인구 요약 API

    - PopulationService.get_summary() 결과를 그대로 반환.
    - 결과 예시:
      [
        {
          "region": "강남구",
          "latest_value": 5800,
          "value": [
            {"year": 2017, "value": 5000},
            {"year": 2018, "value": 5200},
            ...
          ],
          "growth_rate": 0.334
        },
        ...
      ]

    - 대시보드(/dashboard) 테이블, 카드 등에 사용 가능.
    """
    data = population_service.get_summary()
    return jsonify({"status": "success", "data": data})


@api_bp.get("/elderly/forecast/<region>")
def elderly_forecast(region: str):
    """
    (보조용) 특정 구의 예측 데이터 조회 API

    - path parameter로 region을 받는다.
      예: GET /api/v1/elderly/forecast/강남구
    - /predict와 거의 비슷하지만, 관리용/디버깅용 혹은
      내부 화면에서 사용할 수 있는 형태로 남겨둔 엔드포인트.
    """
    data = forecast_service.forecast_region(region)

    # history 자체가 없으면 region 없는 것으로 판단
    if data is None or data.get("history") is None:
        return jsonify(
            {"status": "error", "message": f"Region '{region}' not found"}
        ), 404

    return jsonify({"status": "success", "data": data})


@api_bp.get("/elderly/correlation")
def elderly_correlation():
    """
    상관관계 분석 결과 API

    - CorrelationService.compute() 결과를 반환.
    - /correlation 화면의 heatmap 데이터 소스로 사용 예정.
    - 현재는 heatmap_mock.js로 placeholder를 띄우고 있지만,
      나중에 이 API를 JS에서 호출해서 실제 상관계수 매트릭스를 그리면 된다.
    """
    data = correlation_service.compute()
    return jsonify({"status": "success", "data": data})

@api_bp.get("/elderly-stats/<region_code>/<int:start_year>/<int:end_year>")
def get_elderly_stats_series(region_code: str, start_year: int, end_year: int):
    services = current_app.config.get("services", {})
    feature_stats_service = services.get("feature_stats_service")

    if feature_stats_service is None:
        return jsonify({"error": "service_not_configured"}), 500

    series = feature_stats_service.get_time_series(
        region_code=region_code,
        start_year=start_year,
        end_year=end_year,
    )

    if not series:
        return jsonify(
            {
                "error": "no_data",
                "region_code": region_code,
                "start_year": start_year,
                "end_year": end_year,
            }
        ), 404

    return jsonify(series)

@api_bp.get("/predictions/<region_name>/<int:year>")
def get_prediction(region_name: str, year: int):
    """
    예: GET /api/predictions/강남구/2025

    응답 예:
    {
      "region": "강남구",
      "year": 2025,
      "prediction": 12345.0,
      "source": "rule_based" or "model",
      "history": [...],
    }
    """
    services = current_app.config.get("services", {})
    prediction_service = services.get("prediction_service")

    if prediction_service is None:
        return jsonify({"error": "service_not_configured"}), 500

    result = prediction_service.predict(region_name, year)
    if result is None:
        return jsonify(
            {"error": "no_data", "region": region_name, "year": year}
        ), 404

    return jsonify(result)
