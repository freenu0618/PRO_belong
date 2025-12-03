# web/api/elderly_routes.py
from flask import jsonify, request, current_app
from . import api_bp

from belong.services.population_service import PopulationService
from belong.services.forecast_service import ForecastService
from belong.services.correlation_service import CorrelationService
from belong.repositories.elderly_repo import SqlAlchemyElderlyHistoryRepository
from belong.models.region import Region
from belong.extensions import db

from .routes import api_error, _clean_nan, _validate_year, _validate_year_range

# -----------------------------
# Service 인스턴스 (간단 전역)
# -----------------------------
population_service = PopulationService()
repo = SqlAlchemyElderlyHistoryRepository()
forecast_service = ForecastService(repo=repo)
correlation_service = CorrelationService()


# =========================================================
# 0) /api/prediction (노인 인구 예측 v0.2 - legacy)
# =========================================================
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
    result = forecast_service.forecast_region(
        region=region,
        n_years=n_years,
        horizon=horizon,
    )

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


# =========================================================
# 1) 독거노인 인구 요약
# =========================================================
@api_bp.get("/elderly/population")
def elderly_population():
    """
    독거노인 인구 요약 API
    """
    data = population_service.get_summary()
    return jsonify({"status": "success", "data": data})


# =========================================================
# 2) 구별 노인 인구 예측 (모달)
# =========================================================
@api_bp.get("/elderly/forecast/<region>")
def api_elderly_forecast(region: str):
    """
    GET /api/elderly/forecast/강남구

    응답:
    {
      "status": "success",
      "data": {
        "region": "강남구",
        "history": [...],
        "forecast": [...],
        "message": "..."
      }
    }
    """
    region = region.strip()
    if not region:
        return (
            jsonify(
                {"status": "error", "message": "region 경로 파라미터는 필수입니다."}
            ),
            400,
        )

    data = forecast_service.forecast_region(region)

    # history/forecast 둘 다 비어 있으면 404로 돌려줘도 JS 쪽에서 잘 처리됨
    if not data.get("history") and not data.get("forecast"):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"'{region}' 구의 노인 인구 데이터를 찾을 수 없습니다.",
                    "data": data,
                }
            ),
            404,
        )

    return jsonify({"status": "success", "data": data})


# =========================================================
# 3) 상관관계 분석 (Correlation)
# =========================================================
@api_bp.get("/elderly/correlation")
def elderly_correlation():
    """
    상관관계 분석 결과 API (DB 기반)

    선택 쿼리 파라미터:
      - year_from
      - year_to
      - region_name
    """
    year_from = request.args.get("year_from", type=int)
    year_to = request.args.get("year_to", type=int)
    region_name = request.args.get("region_name", type=str)

    region_ids = None

    if region_name:
        region_row = db.session.query(Region).filter(Region.name == region_name).first()
        if region_row is None:
            return api_error(
                404,
                "region_not_found",
                f"Region '{region_name}' not found",
                region_name=region_name,
            )
        region_ids = [region_row.id]

    raw_data = correlation_service.compute(
        year_from=year_from,
        year_to=year_to,
        region_ids=region_ids,
    )

    if raw_data is None:
        return api_error(
            404,
            "no_data",
            "no correlation data for given filters",
            year_from=year_from,
            year_to=year_to,
            region_name=region_name,
        )

    # NaN / Inf 정리
    data = _clean_nan(raw_data)

    return jsonify({"status": "success", "data": data})


# =========================================================
# 4) ELDERLY_STATS 시계열 API (feature_stats_service 기반)
# =========================================================
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


# =========================================================
# 5) 노인 인구 전체 추세 / TOP5 / 구별 스냅샷
# =========================================================
@api_bp.get("/elderly/trend")
def api_elderly_trend():
    """
    GET /api/elderly/trend?start_year=2017&end_year=2035
    """
    start_year = request.args.get("start_year", type=int) or 2017
    end_year = request.args.get("end_year", type=int) or 2035

    items = forecast_service.get_total_trend(start_year, end_year)
    return jsonify({"status": "success", "items": items})


@api_bp.get("/elderly/top5")
def api_elderly_top5():
    """
    GET /api/elderly/top5?base_year=2023&target_year=2035&by=ratio|absolute
    """
    base_year = request.args.get("base_year", type=int)
    target_year = request.args.get("target_year", type=int)
    by = request.args.get("by", default="ratio")

    if base_year is None or target_year is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "base_year, target_year 파라미터는 필수입니다.",
                }
            ),
            400,
        )

    try:
        items = forecast_service.get_top5(base_year, target_year, by=by)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify({"status": "success", "items": items})


@api_bp.get("/elderly/regions")
def elderly_regions_snapshot():
    """
    특정 연도의 구별 노인 인구 리스트 API.
    예:
      GET /api/elderly/regions?year=2035
    """
    elderly_service = current_app.config["services"]["elderly_service"]

    year = request.args.get("year", type=int)
    if year is None:
        return jsonify({"error": "year 파라미터는 필수입니다."}), 400

    data = elderly_service.get_region_snapshot(year=year)
    return jsonify(data)
