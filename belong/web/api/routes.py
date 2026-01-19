# web/api/routes.py
from flask import jsonify, request, current_app
from . import api_bp
import math
from belong.services.forecast_service import ACTUAL_LAST_YEAR
from .response_utils import success_response, error_response, server_error
# -----------------------------
# 공통 유틸 함수들
# -----------------------------

def _clean_nan(obj):
    """
    JSON으로 보낼 데이터에서 NaN / Inf 를 None으로 치환
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_nan(v) for v in obj]
    return obj


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


# ---- 연도 Validation 상수/함수 ----
MIN_YEAR = 2017
MAX_YEAR = 2035


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


# -----------------------------
# 헬스 체크
# -----------------------------
@api_bp.get("/health")
def health():
    """
    서비스 헬스 체크용 엔드포인트
    """
    return jsonify({"status": "ok"})

# 리스크 맵용 스냅샷 (구별 노인 인구/지표)

@api_bp.get("/dashboard/risk-map")
def dashboard_risk_map():
    year = request.args.get("year", type=int) or ACTUAL_LAST_YEAR

    ok, err = _validate_year(year)
    if not ok:
        return error_response(
            message=err["message"],
            status_code=400,
            error_code=err["code"],
            details=err
        )

    services = current_app.config.get("services", {})
    elderly_service = services.get("elderly_service")

    if elderly_service is None:
        return server_error("서비스가 초기화되지 않았습니다")

    # {year, items: [...] }
    snapshot = elderly_service.get_region_snapshot(year)
    return success_response(_clean_nan(snapshot))

# 특정 구의 연도별 추세

@api_bp.get("/dashboard/region-trend")
def dashboard_region_trend():
    region = request.args.get("region", type=str)
    if not region:
        return error_response(
            message="'region' 파라미터가 필요합니다",
            status_code=400,
            error_code="missing_region"
        )

    start_year = request.args.get("start_year", type=int, default=MIN_YEAR)
    end_year = request.args.get("end_year", type=int, default=ACTUAL_LAST_YEAR)

    ok, err = _validate_year_range(start_year, end_year)
    if not ok:
        return error_response(
            message=err["message"],
            status_code=400,
            error_code=err["code"],
            details=err
        )

    services = current_app.config.get("services", {})
    feature_stats_service = services.get("feature_stats_service")

    if feature_stats_service is None:
        return server_error("서비스가 초기화되지 않았습니다")

    series = feature_stats_service.get_time_series(
        region_code=region,
        start_year=start_year,
        end_year=end_year,
    )

    payload = {
        "region": region,
        "start_year": start_year,
        "end_year": end_year,
        "items": series,
    }
    return success_response(_clean_nan(payload))
