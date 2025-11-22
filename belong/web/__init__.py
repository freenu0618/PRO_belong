from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)
# url_for("web.index") 처럼 쓸 때, 앞의 "web"이 이것
# __name__ : Flask가 템플릿, 정적 파일 등의 상대 경로를 찾을 때 기준

@web_bp.route("/")
def index():
    return render_template("dashboard.html") #templates 폴더 안에서 "dashboard.html" 파일을 찾음.기본 위치는 앱 기준 templates/dashboard.html
# 블루프린트마다 개별 templates 폴더를 둘 수도 있음.
# 브라우저에서 GET / 로 들어오면 이 index 함수가 실행

@web_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@web_bp.route("/region/<region>") # <region> 이라는 동적 URL 파라미터를 사용. URL 경로 변경 조작
def region_detail(region): # 위에 <region>을 Flask가 함수인자인()안에 region에 자동으로 넣어줌
    return render_template("region_deatil.html", region=region) 
# EX) /region/jongno → region 변수에 "jongno" 가 들어감
# 템플릿에서 region 변수를 {{ region }}으로 사용가능 jinja2언어로
# region변수를 DB조회,데이버 분석, 조건 분기 등으로 활용

@web_bp.route("/correlation")
def correlation():
    return render_template("correlation.html")