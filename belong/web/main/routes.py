from flask import render_template, redirect, url_for, request, current_app, abort
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
    )