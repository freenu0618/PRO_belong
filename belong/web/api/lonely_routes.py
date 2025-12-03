# web/api/lonely_routes.py
from flask import jsonify, request, current_app
from . import api_bp

from belong.services.lonely_forecast_service import LonelyForecastService
from .routes import api_error, _validate_year

lonely_forecast_service = LonelyForecastService()


# =========================================================
# 1) 고독사 전체 추세
# =========================================================
@api_bp.get("/lonely/trend")
def api_lonely_trend():
    """
    GET /api/lonely/trend?start_year=2017&end_year=2035
    """
    start_year = request.args.get("start_year", type=int) or 2017
    end_year = request.args.get("end_year", type=int) or 2035

    items = lonely_forecast_service.get_trend(start_year, end_year)
    return jsonify({"status": "success", "items": items})


# =========================================================
# 2) 구별 고독사 예측 (모달)
# =========================================================
@api_bp.get("/lonely/forecast")
def api_lonely_forecast():
    """
    GET /api/lonely/forecast?region=강남구

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
    region = request.args.get("region", "", type=str).strip()
    if not region:
        return (
            jsonify(
                {"status": "error", "message": "region 쿼리 파라미터는 필수입니다."}
            ),
            400,
        )

    data = lonely_forecast_service.forecast_region(region)

    if not data.get("history") and not data.get("forecast"):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"'{region}' 구의 고독사 실측/예측 데이터를 찾을 수 없습니다.",
                    "data": data,
                }
            ),
            404,
        )

    return jsonify({"status": "success", "data": data})


# =========================================================
# 3) 고독사 TOP5 (증가율 / 증가 인원수)
# =========================================================
@api_bp.get("/lonely/top5")
def api_lonely_top5():
    """
    GET /api/lonely/top5?base_year=2023&target_year=2035&by=ratio|absolute
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
        items = lonely_forecast_service.get_top5(base_year, target_year, by=by)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify({"status": "success", "items": items})


# =========================================================
# 4) PREDICTION_RESULT 연동 API
#    (ML 예측 + 저장 / 히스토리 조회)
# =========================================================
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
