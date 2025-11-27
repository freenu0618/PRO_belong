from flask import render_template, redirect, url_for, request
from . import web_bp

@web_bp.route("/")
def index():
    return render_template("index.html") #templates 폴더 안에서 "dashboard.html" 파일을 찾음.기본 위치는 앱 기준 templates/dashboard.html
# 블루프린트마다 개별 templates 폴더를 둘 수도 있음.
# 브라우저에서 GET / 로 들어오면 이 index 함수가 실행

@web_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@web_bp.route("/region/<region>")
def region_detail(region):
    """
    특정 지역 예측 결과 페이지
    URL 예: /region/강남구?year=2026

    - path 파라미터: region
    - querystring: year
    """
    year = request.args.get("year", type=int)

    return render_template(
        "region_detail.html",
        region=region,
        year=year,
    )

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