from flask import Blueprint

api_bp = Blueprint('api', __name__, template_folder="templates", url_prefix="/api",
    static_folder="../../static")

from . import routes # noqa
# Blueprint는 import 되는 순간 라우트가 등록됨
# 그래서 from . import routes 가 실행되어야  api_bp에 연결된 라우트들이 완성됨