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

# 새 CorrelationService는 내부에서 db.session을 사용함
correlation_service = CorrelationService()

# 공통 API 에러 응답 헬퍼
def api_error(status_code: int, code: str, message: str, **details):
    """
    통일된 API 에러 응답 형식 생성 헬퍼.

    예:
        return api_error(400, "invalid_input", "year is out of range", value=2099)
    """
    payload = {
        "error": code,
        "message": message,
    }
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


# ---- 입력값 Validation 설정 ----
# 상수 설정해서 최소연도, 최대 연도 설정
MIN_YEAR = 2017
MAX_YEAR = 2050

def _validate_year(year: int):
    """
    단일 연도(year)에 대한 범위 검증.
    유효하면 (True, None), 아니면 (False, error_detail_dict)를 반환.
    """
    if year < MIN_YEAR or year > MAX_YEAR:
        return False, {
            "code": "year_out_of_range",
            "message": f"year must be between {MIN_YEAR} and {MAX_YEAR}",
            "value": year,
        }
    return True, None


def _validate_year_range(start_year: int, end_year: int):
    """
    (start_year, end_year) 구간에 대한 검증.
    - start_year <= end_year
    - 둘 다 MIN_YEAR ~ MAX_YEAR 범위
    """
    ok_start, err_start = _validate_year(start_year)
    ok_end, err_end = _validate_year(end_year)

    if not ok_start:
        return False, {
            "code": "invalid_start_year",
            "message": "start_year is invalid",
            "detail": err_start,
        }

    if not ok_end:
        return False, {
            "code": "invalid_end_year",
            "message": "end_year is invalid",
            "detail": err_end,
        }

    if start_year > end_year:
        return False, {
            "code": "start_after_end",
            "message": "start_year must be less than or equal to end_year",
            "start_year": start_year,
            "end_year": end_year,
        }

    return True, None


@api_bp.get("/prediction")
def predict():
    """
    독거노인 인구 예측 API (v0.2)

    쿼리 파라미터:
      - region: 필수, '강남구' 등
      - horizon: 선택, 'short' 또는 'long' (기본: 'short')
      - years: 선택, 정수. 주어지면 horizon보다 우선.

    예:
      GET /api/predict?region=강남구                -> short(3년) 예측
      GET /api/predict?region=강남구&horizon=long  -> long(10년) 예측
      GET /api/predict?region=강남구&years=5       -> 5년 예측
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

    - 브라우저나 모니터링 도구에서 /api/health 를 호출해서
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


@api_bp.get("/elderly/forecast/<region>")  # 기존 경로 유지
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
    상관관계 분석 결과 API (DB 기반)

    - ELDERLY_STATS 테이블에서 데이터를 조회해서
      CorrelationService.compute()로 상관계수를 계산.
    - /correlation 화면의 heatmap/막대 그래프 데이터 소스로 사용.

    선택 쿼리 파라미터:
      - year_from: 시작 연도 (예: 2017)
      - year_to:   종료 연도 (예: 2023)
      (둘 다 없으면 전체 연도 대상으로 계산)
    """
    year_from = request.args.get("year_from", type=int)
    year_to = request.args.get("year_to", type=int)

    data = correlation_service.compute(
        year_from=year_from,
        year_to=year_to,
        region_ids=None,  # 필요하면 추후 region_code → region_id 매핑해서 넣을 수 있음
    )
    return jsonify({"status": "success", "data": data})


@api_bp.get("/predictions/<region>/<int:year>")
def get_prediction(region: str, year: int):
    """
    예: GET /api/predictions/강남구/2025
    → 예측만 수행 (저장은 안 해도 됨)
    """
    ok, err = _validate_year(year)
    if not ok:
        return api_error(400, "invalid_input", "year is out of allowed range", **err)

    services = current_app.config["services"]
    prediction_service = services.get("prediction_service")
    if prediction_service is None:
        return api_error(500, "service_not_configured",
                         "prediction_service is not configured")

    result = prediction_service.predict(region, year)
    if result is None:
        return api_error(404, "no_data",
                         "no prediction data available for given region and year",
                         region=region, year=year)

    return jsonify(result)


@api_bp.get("/elderly-stats/<region_code>/<int:start_year>/<int:end_year>")
def get_elderly_stats_series(region_code: str, start_year: int, end_year: int):
    # 1) 입력값 검증
    ok, error_detail = _validate_year_range(start_year, end_year)
    if not ok:
        return api_error(
            400,
            "invalid_input",
            "invalid year range",
            **error_detail,
        )

    services = current_app.config.get("services", {})
    feature_stats_service = services.get("feature_stats_service")

    if feature_stats_service is None:
        return api_error(
            500,
            "service_not_configured",
            "feature_stats_service is not configured in app.config['services']",
        )

    series = feature_stats_service.get_time_series(
        region_code=region_code,
        start_year=start_year,
        end_year=end_year,
    )

    if not series:
        return api_error(
            404,
            "no_data",
            "no elderly stats found for given region and year range",
            region_code=region_code,
            start_year=start_year,
            end_year=end_year,
        )

    return jsonify(series)


@api_bp.post("/predictions/<region>/<int:year>")
def create_prediction(region: str, year: int):
    """
    예: POST /api/predictions/강남구/2025
    → 예측을 수행하고 PREDICTION_RESULT에 저장
    """
    ok, err = _validate_year(year)
    if not ok:
        return api_error(400, "invalid_input", "year not valid", **err)

    services = current_app.config.get("services", {})
    prediction_service = services.get("prediction_service")
    if prediction_service is None:
        return api_error(
            500,
            "service_not_configured",
            "prediction_service is not configured in app.config['services']",
        )

    result = prediction_service.predict_and_store(region, year)
    if result is None:
        return api_error(
            404,
            "no_data",
            "prediction unavailable",
            region=region,
            year=year,
        )

    return jsonify({"saved": True, "result": result})


@api_bp.get("/predictions/history/<region>")
def get_prediction_history(region: str):
    repo = current_app.config["services"]["prediction_repo"]
    rows = repo.list_by_region(region)

    return jsonify([
        {
            "region": r.region_name,
            "year": r.year,
            "prediction": r.prediction_value,
            "source": r.source,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ])
