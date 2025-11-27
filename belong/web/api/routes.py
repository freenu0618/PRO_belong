from flask import jsonify, request, current_app  # 딕셔너리를 JSON 응답으로 감싸주는 유틸
from . import api_bp
from belong.services.population_service import PopulationService
from belong.services.forecast_service import ForecastService
from belong.services.correlation_service import CorrelationService
from belong.repositories.elderly_repo import SqlAlchemyElderlyHistoryRepository
from belong.models.region import Region
from belong.extensions import db
from belong.repositories.prediction_repo import PredictionRepository
from belong.services.lonely_forecast_service import LonelyForecastService
import math
from werkzeug.security import generate_password_hash, check_password_hash
from belong.models.user import User

# Service 인스턴스들은 지금은 간단히 전역으로 올려도 괜찮음
population_service = PopulationService()
# Oracle 연결을 우선 시도하고, 실패하면 InMemory로 fallback
repo = SqlAlchemyElderlyHistoryRepository()
forecast_service = ForecastService(repo=repo)
lonely_forecast_service = LonelyForecastService()
# 새 CorrelationService는 내부에서 db.session을 사용함
correlation_service = CorrelationService()

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
    """
    return jsonify({"status": "ok"})


@api_bp.get("/elderly/population")
def elderly_population():
    """
    독거노인 인구 요약 API
    """
    data = population_service.get_summary()
    return jsonify({"status": "success", "data": data})


@api_bp.get("/elderly/forecast/<region>")  # 기존 경로 유지
def elderly_forecast(region: str):
    """
    (보조용) 특정 구의 예측 데이터 조회 API
    """
    data = forecast_service.forecast_region(region)

    if data is None or data.get("history") is None:
        return jsonify(
            {"status": "error", "message": f"Region '{region}' not found"}
        ), 404

    return jsonify({"status": "success", "data": data})


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

    # 🔥 NaN / Inf 정리
    data = _clean_nan(raw_data)

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

@api_bp.get("/elderly/trend")
def elderly_trend():
    """
    노인 인구 전체 추세 (2017~2050) API.
    예:
      GET /api/elderly/trend?start_year=2017&end_year=2050
    """
    elderly_service = current_app.config["services"]["elderly_service"]

    start_year = request.args.get("start_year", default=2017, type=int)
    end_year = request.args.get("end_year", default=2050, type=int)

    data = elderly_service.get_total_trend(start_year=start_year, end_year=end_year)
    return jsonify(data)

@api_bp.get("/elderly/top5")
def elderly_top5():
    """
    노인 인구 증가 TOP5 API.
    예:
      GET /api/elderly/top5?base_year=2023&target_year=2050&by=ratio
      GET /api/elderly/top5?base_year=2023&target_year=2050&by=absolute
    """
    elderly_service = current_app.config["services"]["elderly_service"]

    base_year = request.args.get("base_year", type=int)
    target_year = request.args.get("target_year", type=int)
    by = request.args.get("by", default="ratio", type=str)

    if base_year is None or target_year is None:
        return (
            jsonify(
                {
                    "error": "base_year와 target_year는 필수입니다.",
                }
            ),
            400,
        )

    if by not in ("ratio", "absolute"):
        return jsonify({"error": "by 파라미터는 'ratio' 또는 'absolute' 이어야 합니다."}), 400

    data = elderly_service.get_top5_growth(base_year=base_year, target_year=target_year, by=by)
    return jsonify(data)

@api_bp.get("/elderly/regions")
def elderly_regions_snapshot():
    """
    특정 연도의 구별 노인 인구 리스트 API.
    예:
      GET /api/elderly/regions?year=2050
    """
    elderly_service = current_app.config["services"]["elderly_service"]

    year = request.args.get("year", type=int)
    if year is None:
        return jsonify({"error": "year 파라미터는 필수입니다."}), 400

    data = elderly_service.get_region_snapshot(year=year)
    return jsonify(data)

# ============================
#  Auth API (signup / login / logout)
# ============================

@api_bp.post("/auth/signup")
def api_signup():
    """
    POST /api/auth/signup
    body: { "username": "...", "email": "...", "password": "..." }
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    # 1) 입력 검증
    if not username or not email or not password:
        return jsonify({
            "status": "error",
            "message": "아이디, 이메일, 비밀번호를 모두 입력해주세요."
        }), 400

    # 2) 중복 체크
    existing = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing:
        return jsonify({
            "status": "error",
            "message": "이미 사용 중인 아이디 또는 이메일입니다."
        }), 409

    # 3) 유저 생성 및 저장
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "status": "success",
        "data": {
            "username": user.username,
            "email": user.email,
        }
    }), 201


@api_bp.post("/auth/login")
def api_login():
    """
    POST /api/auth/login
    body: { "username": "...", "password": "..." }
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "아이디와 비밀번호를 모두 입력해주세요."
        }), 400

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password(password):
        # 아이디 or 비밀번호 틀린 경우
        return jsonify({
            "status": "error",
            "message": "아이디 또는 비밀번호가 올바르지 않습니다."
        }), 401

    # 여기서는 서버 세션 대신, 프론트에서 localStorage로만 처리하니까
    # 간단히 유저 정보만 내려준다.
    return jsonify({
        "status": "success",
        "data": {
            "username": user.username,
            "email": user.email,
        }
    }), 200


@api_bp.post("/auth/logout")
def api_logout():
    """
    POST /api/auth/logout
    - 서버 세션을 안 쓰고 있으니, 그냥 성공 응답만 주면 됨.
    - 프론트에서는 localStorage.removeItem('belong_user') 같은 식으로 처리.
    """
    return jsonify({
        "status": "success",
        "message": "로그아웃 되었습니다."
    }), 200

@api_bp.get("/lonely/forecast")
def api_lonely_forecast():
    """
    고독사 구별 실측/예측 시계열 API.

    예:
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
    region = request.args.get("region")

    if not region:
        return jsonify({
            "status": "error",
            "message": "region 파라미터는 필수입니다. (예: 강남구)"
        }), 400

    data = lonely_forecast_service.forecast_region(region)

    # 데이터가 아예 없을 때
    if not data.get("history") and not data.get("forecast"):
        return jsonify({
            "status": "error",
            "message": f"'{region}' 구의 고독사 실측/예측 데이터를 찾을 수 없습니다.",
            "data": data,
        }), 404

    return jsonify({
        "status": "success",
        "data": data,
    })
