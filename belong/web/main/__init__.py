from flask import Blueprint, render_template

web_bp = Blueprint(
    "web",
    __name__,
    template_folder="templates"
)

# url_for("web.index") 처럼 쓸 때, 앞의 "web"이 이것
# __name__ : Flask가 템플릿, 정적 파일 등의 상대 경로를 찾을 때 기준

from . import routes