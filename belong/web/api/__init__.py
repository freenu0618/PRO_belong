# web/api/__init__.py
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# ✅ 에러 핸들러 등록
from belong.web.api.error_handlers import register_error_handlers
register_error_handlers(api_bp)

# 여기서 기능별 routes 모듈들을 불러오면,
# 각 모듈이 api_bp에 @api_bp.get(...), @api_bp.post(...)를 등록하게 됨.
from . import elderly_routes  # noqa: F401
from . import lonely_routes   # noqa: F401
from . import auth_routes     # noqa: F401
from . import routes          # 기존 공통 API가 있으면 유지
from . import ai_route
from . import tuning_route
