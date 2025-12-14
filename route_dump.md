

# FILE: belong/web/api/__init__.py
```# web/api/__init__.py
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# 여기서 기능별 routes 모듈들을 불러오면,
# 각 모듈이 api_bp에 @api_bp.get(...), @api_bp.post(...)를 등록하게 됨.
from . import elderly_routes  # noqa: F401
from . import lonely_routes   # noqa: F401
from . import auth_routes     # noqa: F401
from . import routes          # 기존 공통 API가 있으면 유지
from . import ai_route```

# FILE: belong/web/api/ai_route.py
```from flask import jsonify, request
from . import api_bp

from belong.services.ai_service import AIService

ai_service = AIService()

def _parse_request():
    """
    공통 Request 포맷

    {
      "text": "분석할 텍스트 or 질문",
      "options": { ... }
    }
    """
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    options = data.get("options") or {}
    return text, options

def _make_ai_response(service: str, input_text: str, result: dict,
                      ok: bool = True, mode: str = "mock"):
    """
    공통 Response 포맷

    {
      "ok": true,
      "service": "sentiment",
      "input": { "text": "..." },
      "result": { ... },
      "debug": { "mode": "mock" }
    }
    """
    return jsonify(
        {
            "ok": ok,
            "service": service,
            "input": {"text": input_text},
            "result": result,
            "debug": {"mode": mode},
        }
    )

# 미니1: 감정 분석
# POST /api/ai/sentiment
@api_bp.post("/ai/sentiment")
def api_ai_sentiment():
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="sentiment",
            input_text=text,
            result={"error": "text 필드는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    result = ai_service.analyze_sentiment(text)
    return _make_ai_response(
        service="sentiment",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200

# 미니2: 개체(객체) 분석
# POST /api/ai/entities
@api_bp.post("/ai/entities")
def api_ai_entities():
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="entities",
            input_text=text,
            result={"error": "text 필드는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    result = ai_service.analyze_entities(text)
    return _make_ai_response(
        service="entities",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200

# 미니3: 질의응답
# POST /api/ai/qa
@api_bp.post("/ai/qa")
def api_ai_qa():
    question, options = _parse_request()
    context = (options.get("context") or "").strip()

    if not question or not context:
        return _make_ai_response(
            service="qa",
            input_text=question,
            result={
                "error": "text(질문)와 options.context(지문)는 모두 필수입니다."
            },
            ok=False,
            mode="mock",
        ), 400

    result = ai_service.answer_question(question=question, context=context)
    return _make_ai_response(
        service="qa",
        input_text=question,
        result=result,
        ok=True,
        mode="mock",
    ), 200

# 미니4: 텍스트 요약
# POST /api/ai/summary
@api_bp.post("/ai/summary")
def api_ai_summary():
    """
    텍스트 요약 API
    Body:
      {
        "text": "...",
        "options": {
          "max_length": 64,
          "min_length": 16
        }
      }
    """
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="summary",
            input_text=text,
            result={"error": "text(요약할 텍스트)는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    max_length = int(options.get("max_length", 64))
    min_length = int(options.get("min_length", 16))

    result = ai_service.summarize(
        text=text,
        max_length=max_length,
        min_length=min_length,
    )

    return _make_ai_response(
        service="summary",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200

# 미니5: 번역
# POST /api/ai/translate
@api_bp.post("/ai/translate")
def api_ai_translate():
    """
    번역 API
    Body:
      {
        "text": "...",
        "options": {
          "direction": "ko-en" or "en-ko"
        }
      }
    """
    text, options = _parse_request()

    if not text:
        return _make_ai_response(
            service="translate",
            input_text=text,
            result={"error": "text(번역할 텍스트)는 필수입니다."},
            ok=False,
            mode="mock",
        ), 400

    direction = (options.get("direction") or "ko-en").strip()

    result = ai_service.translate(
        text=text,
        direction=direction,
    )

    return _make_ai_response(
        service="translate",
        input_text=text,
        result=result,
        ok=True,
        mode="mock",
    ), 200
```

# FILE: belong/web/api/auth_routes.py
```# web/api/auth_routes.py
from flask import jsonify, request
from . import api_bp

from belong.services.auth_service import AuthService

auth_service = AuthService()  # 전역으로 한 번 생성


@api_bp.post("/auth/signup")
def api_signup():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # (필수값 체크는 route에서 해도 OK)
    if not username or not email or not password:
        return jsonify({
            "status": "error",
            "message": "아이디, 이메일, 비밀번호는 모두 필수입니다."
        }), 400

    ok, msg, user = auth_service.signup(username, email, password)

    if not ok:
        # 중복, 비밀번호 규칙 위반 등
        return jsonify({"status": "error", "message": msg}), 400

    return jsonify({
        "status": "success",
        "message": msg,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }), 201


@api_bp.post("/auth/login")
def api_login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "아이디와 비밀번호를 입력해주세요."
        }), 400

    ok, msg, user = auth_service.login(username, password)

    if not ok:
        return jsonify({"status": "error", "message": msg}), 401

    return jsonify({
        "status": "success",
        "message": msg,
        "data": {
            "id": user.id,
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
```

# FILE: belong/web/api/elderly_routes.py
```# web/api/elderly_routes.py
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
```

# FILE: belong/web/api/lonely_routes.py
```# web/api/lonely_routes.py
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
```

# FILE: belong/web/api/routes.py
```# web/api/routes.py
from flask import jsonify, request, current_app
from . import api_bp
import math
from belong.services.forecast_service import ACTUAL_LAST_YEAR
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
        return api_error(400, err["code"], err["message"], detail=err)

    services = current_app.config.get("services", {})
    elderly_service = services.get("elderly_service")

    if elderly_service is None:
        return api_error(
            500,
            "service_not_configured",
            "elderly_service is not registered in app.services",
        )

    # {year, items: [...] }
    snapshot = elderly_service.get_region_snapshot(year)
    return jsonify(_clean_nan(snapshot))

# 특정 구의 연도별 추세

@api_bp.get("/dashboard/region-trend")
def dashboard_region_trend():
    region = request.args.get("region", type=str)
    if not region:
        return api_error(400, "missing_region", "query parameter 'region' is required")

    start_year = request.args.get("start_year", type=int, default=MIN_YEAR)
    end_year = request.args.get("end_year", type=int, default=ACTUAL_LAST_YEAR)

    ok, err = _validate_year_range(start_year, end_year)
    if not ok:
        return api_error(400, err["code"], err["message"], detail=err)

    services = current_app.config.get("services", {})
    feature_stats_service = services.get("feature_stats_service")

    if feature_stats_service is None:
        return api_error(
            500,
            "service_not_configured",
            "feature_stats_service is not registered in app.services",
        )

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
    return jsonify(_clean_nan(payload))
```

# FILE: belong/web/main/routes.py
```from flask import render_template, redirect, url_for, request, current_app, abort
from . import web_bp
from belong.services.forecast_service import ACTUAL_LAST_YEAR

@web_bp.route("/")
def index():
    return render_template("index.html") #templates 폴더 안에서 "dashboard.html" 파일을 찾음.기본 위치는 앱 기준 templates/dashboard.html
# 블루프린트마다 개별 templates 폴더를 둘 수도 있음.
# 브라우저에서 GET / 로 들어오면 이 index 함수가 실행

@web_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@web_bp.route("/region")
def region():
    """
    지역/연도 입력 폼 페이지
    -> region.html 렌더링
    """
    return render_template("region.html")

@web_bp.route("/correlation")
def correlation():
    return render_template("correlation.html")

# -------------------------
# 🔐 로그인 페이지(UI)
# -------------------------
@web_bp.route("/login")
def login():
    return render_template("auth/login.html")


# -------------------------
# 📝 회원가입 페이지(UI)
# -------------------------
@web_bp.route("/signup")
def signup():
    return render_template("auth/signup.html")


# -------------------------
# 🚪 로그아웃 (UI only, JS에서 localStorage 삭제)
# -------------------------
@web_bp.route("/logout")
def logout():
    # UI 기준: JS에서 localStorage 제거 후 메인으로 이동
    return redirect(url_for("web.index"))

@web_bp.get("/ai")
def ai_home():
    """
    AI 서비스 허브 페이지
    - ai_tool.html을 사용해서
    - 내부에서 감정분석/개체분석/요약/QA 등을 선택하게 만들 예정
    """
    return render_template(
        "ai_tool.html",   # 실제 경로에 맞게 수정: "ai/ai_tool.html" 일 수도 있음
        page_title="AI 서비스",
        heading="AI 서비스 허브",
        description="번역, 감정 분석, 개체 분석, 텍스트 요약, 질의응답 AI 도구를 한 곳에서 사용할 수 있습니다.",
    )

@web_bp.get("/regions/<region_name>")
def region_detail(region_name):
    """
    지역 상세 페이지
    - 백엔드 서비스 호출 없이 템플릿에 이름만 넘긴다.
    - 실제 데이터 로딩은 전부 JS에서 /api/elderly/forecast, /api/lonely/forecast로 처리.
    """
    return render_template(
        "web/region_detail.html",
        region_name=region_name,
    )```