

# FILE: belong/web/main/templates/auth/login.html
```{% extends "base.html" %}
{% block title %}로그인{% endblock %}

{% block content %}
<div class="auth-page page-gradient">
  <div class="auth-card row g-0">
    <!-- LEFT PANEL -->
    <div class="auth-left col-md-6 d-none d-md-block position-relative">
      <div class="auth-left-overlay position-absolute top-0 start-0 end-0 bottom-0 p-4 d-flex flex-column justify-content-between">
        <div>
          <div class="auth-badge mb-3">
            <span class="auth-dot"></span>
            <span>Belong · 고독사 예측 서비스</span>
          </div>
          <h2 class="auth-title-main mb-3">
            함께하면,<br>
            <span class="auth-highlight">보이지 않던 위험</span>이 보입니다.
          </h2>
          <p class="mb-0" style="max-width: 260px; font-size: 0.9rem;">
            1인 고령가구 데이터를 기반으로,<br>
            고독사 위험을 미리 예측하고 대응할 수 있도록 돕는 서비스입니다.
          </p>
        </div>
        <div class="auth-footer-text">
          이미 계정이 있으신가요?<br>
          <span class="text-slate-200">지금 로그인하고 대시보드에서 지역별 현황을 확인해 보세요.</span>
        </div>
      </div>
    </div>

    <!-- RIGHT PANEL -->
    <div class="auth-right col-md-6 p-4 p-md-5">
      <div class="mb-4 text-center text-md-start">
        <h3 class="fw-bold mb-1">Belong에 로그인</h3>
        <p class="mb-0 text-secondary" style="font-size: 0.9rem;">
          계정을 입력하고 서비스를 계속 이용하세요.
        </p>
      </div>

      <div id="login-error" class="alert alert-danger py-2 px-3" style="display:none; font-size:0.9rem;"></div>

      <form id="login-form" novalidate>
        <div class="mb-3">
          <label class="form-label auth-input-label">아이디</label>
          <input type="text" class="form-control auth-input" id="username" required autocomplete="username">
        </div>

        <div class="mb-2">
          <label class="form-label auth-input-label">비밀번호</label>
          <input type="password" class="form-control auth-input" id="password" required autocomplete="current-password">
        </div>

        <div class="d-flex justify-content-between align-items-center mb-4" style="font-size: 0.85rem;">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="rememberMe">
            <label class="form-check-label text-secondary" for="rememberMe">
              로그인 상태 유지
            </label>
          </div>
          <a href="#" class="auth-link opacity-75" onclick="return false;">비밀번호 찾기</a>
        </div>

        <button type="submit" class="btn auth-btn-primary w-100 py-2 mb-3">
          로그인
        </button>

        <div class="text-center auth-footer-text">
          아직 계정이 없으신가요?
          <a href="{{ url_for('web.signup') }}" class="auth-link ms-1">회원가입</a>
        </div>
      </form>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
  <script src="{{ url_for('static', filename='js/login.js') }}"></script>
{% endblock %}
```

# FILE: belong/web/main/templates/auth/signup.html
```{% extends "base.html" %}
{% block title %}회원가입{% endblock %}

{% block content %}
<div class="auth-page page-gradient">
  <div class="auth-card row g-0">
    <!-- LEFT PANEL -->
    <div class="auth-left col-md-6 d-none d-md-block position-relative">
      <div class="auth-left-overlay position-absolute top-0 start-0 end-0 bottom-0 p-4 d-flex flex-column justify-content-between">
        <div>
          <div class="auth-badge mb-3">
            <span class="auth-dot"></span>
            <span>Belong · 함께하는 시작</span>
          </div>
          <h2 class="auth-title-main mb-3">
            한 사람의 연결이,<br>
            <span class="auth-highlight">많은 삶을 지켜냅니다.</span>
          </h2>
          <p class="mb-0" style="max-width: 260px; font-size: 0.9rem;">
            지금 계정을 만들고, 지역별 고독사 위험과 노인 인구 현황을 한눈에 확인해 보세요.
          </p>
        </div>
        <div class="auth-footer-text">
          이미 계정이 있으신가요?
          <br>
          <span class="text-slate-200">로그인 후 대시보드에서 현재 상황을 바로 확인할 수 있습니다.</span>
        </div>
      </div>
    </div>

    <!-- RIGHT PANEL -->
    <div class="auth-right col-md-6 p-4 p-md-5">
      <div class="mb-4 text-center text-md-start">
        <h3 class="fw-bold mb-1">Belong 회원가입</h3>
        <p class="mb-0 text-secondary" style="font-size: 0.9rem;">
          기본 정보를 입력하고 계정을 생성하세요.
        </p>
      </div>

      <div id="signup-error" class="alert alert-danger py-2 px-3" style="display:none; font-size:0.9rem;"></div>

      <form id="signup-form" novalidate>
        <div class="mb-3">
          <label class="form-label auth-input-label">아이디</label>
          <input type="text" class="form-control auth-input" id="username" required autocomplete="username">
        </div>

        <div class="mb-3">
          <label class="form-label auth-input-label">이메일</label>
          <input type="email" class="form-control auth-input" id="email" required autocomplete="email">
        </div>

        <div class="mb-3">
          <label class="form-label auth-input-label">비밀번호</label>
          <input type="password" class="form-control auth-input" id="password1" required autocomplete="new-password">
        </div>

        <div class="mb-2">
          <label class="form-label auth-input-label">비밀번호 확인</label>
          <input type="password" class="form-control auth-input" id="password2" required autocomplete="new-password">
          <small id="pw-match-msg" class="fw-bold mt-1 d-block" style="display:none; font-size:0.8rem;"></small>
        </div>

        <div class="form-check mb-4" style="font-size: 0.85rem;">
          <input class="form-check-input" type="checkbox" id="termsCheck" required>
          <label class="form-check-label text-secondary" for="termsCheck">
            <a href="#" onclick="return false;" class="auth-link">개인정보 처리방침</a> 및 이용약관에 동의합니다.
          </label>
        </div>

        <button type="submit" class="btn auth-btn-primary w-100 py-2 mb-3">
          회원가입
        </button>

        <div class="text-center auth-footer-text">
          이미 계정이 있으신가요?
          <a href="{{ url_for('web.login') }}" class="auth-link ms-1">로그인</a>
        </div>
      </form>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
  <script src="{{ url_for('static', filename='js/signup.js') }}"></script>
{% endblock %}
```

# FILE: belong/web/main/templates/base.html
```<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>{% block title %}Belong - 고독사 안심 프로젝트{% endblock %}</title>

    <!-- Bootstrap 5.x CSS (CDN) -->
    <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
    >

    <!-- Pretendard -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">

    <!-- Global CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
  </head>
  <body>
    <div class="page-grid">

      <!-- 헤더 -->
      <header class="site-header">
        {% block header %}
          <div class="page-container py-2">
            {% include "navbar.html" %}
          </div>
        {% endblock %}
      </header>

      <!-- 메인 콘텐츠 -->
      <main class="site-main">
        {% block content %}{% endblock %}
      </main>

      <!-- 푸터 -->
      <footer class="site-footer">
        {% block footer %}
          <div class="page-container footer-inner py-3">
            <small class="text-muted">© 2025 Belong Project</small>
          </div>
        {% endblock %}
      </footer>

    </div>

    <!-- ✅ 전역: 준비중 모달 -->
    <div class="modal fade" id="comingSoonModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4">
          <div class="modal-header">
            <h5 class="modal-title fw-bold" id="comingSoonTitle">준비중</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="닫기"></button>
          </div>
          <div class="modal-body">
            <p class="mb-2" id="comingSoonBody" style="line-height:1.7;">
              현재는 <strong>대시보드</strong>와 <strong>AI 챗봇 서비스(5기능)</strong>를 중심으로 운영 중입니다.
              <br>
              선택하신 기능은 UI 구조까지 준비해두었고, 다음 단계에서 연결될 예정입니다.
            </p>
            <div class="small text-muted" id="comingSoonHint">
              원하시면 먼저: 대시보드로 데이터 확인 → AI 챗봇으로 텍스트 작업을 진행해보세요.
            </div>
          </div>
          <div class="modal-footer">
            <a class="btn btn-outline-primary rounded-4" href="{{ url_for('web.dashboard') }}">대시보드</a>
            <a class="btn btn-primary rounded-4" href="{{ url_for('web.ai_home') }}">AI 챗봇</a>
            <button type="button" class="btn btn-light rounded-4" data-bs-dismiss="modal">닫기</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bootstrap JS (bundle - Popper 포함) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

    <!-- 전역 JS -->
    <script src="{{ url_for('static', filename='js/app_ui.js') }}"></script>

    <!-- ✅ JWT 로그인 상태 네비 토글/로그아웃 처리 -->
    <script src="{{ url_for('static', filename='js/auth_ui.js') }}"></script>

    {% block extra_js %}{% endblock %}
  </body>
</html>
{% block scripts %}{% endblock %}
{% block extra_js %}{% endblock %}
```

# FILE: belong/web/main/templates/ai_tool.html
```{# templates/ai_tool.html #}
{% extends "base.html" %}

{% block title %}AI 챗봇 서비스 - Belong{% endblock %}

{% block page_id %}ai{% endblock %}
{% block body_class %}ai-page{% endblock %}

{% block content %}
<section class="section py-4 py-lg-5">
  <div class="page-container">

    <!-- 소개 -->
    <div class="mb-4 ai-hero">
      <div class="text-muted small mb-2">AI Chatbot Service</div>
      <h1 class="ai-feature-title">AI 챗봇 서비스</h1>
      <p class="text-muted mb-0" style="line-height:1.7;">
        번역 · 감정분석 · 텍스트 요약 · 질의응답 · 개체분석(5기능)을 한 화면에서 사용할 수 있습니다.
      </p>
      <div class="mt-3 small text-muted">
        사용법: 기능 선택 → 텍스트 입력 → 실행
      </div>
    </div>

    <!-- 빠른 선택(5기능) -->
    <div class="row g-3 mb-4 ai-feature-grid">
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card h-100 rounded-4 border-0 shadow-sm ai-feature-card">
          <div class="card-body p-4 ai-feature-card">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <div class="fw-bold">😊 감정 분석</div>
              <span class="badge text-bg-light">sentiment</span>
            </div>
            <p class="ai-feature-desc" style="line-height:1.6;">
              문장의 감정(긍/부정 등)을 분석합니다.
            </p>
            <button class="btn btn-outline-primary rounded-4 ai-quick-select"
                    type="button"
                    data-ai-service="sentiment">
              이 기능으로 시작
            </button>
          </div>
        </div>
      </div>

      <div class="col-12 col-md-6 col-lg-4">
        <div class="card h-100 rounded-4 border-0 shadow-sm ai-feature-card">
          <div class="card-body p-4 ai-feature-card">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <div class="fw-bold">🏷️ 개체 분석</div>
              <span class="badge text-bg-light">entities</span>
            </div>
            <p class="ai-feature-desc" style="line-height:1.6;">
              문장에서 인물/기관/장소 등 핵심 엔티티를 추출합니다.
            </p>
            <button class="btn btn-outline-primary rounded-4 ai-quick-select"
                    type="button"
                    data-ai-service="entities">
              이 기능으로 시작
            </button>
          </div>
        </div>
      </div>

      <div class="col-12 col-md-6 col-lg-4">
        <div class="card h-100 rounded-4 border-0 shadow-sm ai-feature-card">
          <div class="card-body p-4 ai-feature-card">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <div class="fw-bold">❓ 질의 응답</div>
              <span class="badge text-bg-light">qa</span>
            </div>
            <p class="ai-feature-desc" style="line-height:1.6;">
              질문 + 지문(Context)을 입력하면 답변을 생성합니다.
            </p>
            <button class="btn btn-outline-primary rounded-4 ai-quick-select"
                    type="button"
                    data-ai-service="qa">
              이 기능으로 시작
            </button>
          </div>
        </div>
      </div>

      <div class="col-12 col-md-6 col-lg-6">
        <div class="card h-100 rounded-4 border-0 shadow-sm ai-feature-card">
          <div class="card-body p-4 ai-feature-card">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <div class="fw-bold">🌐 번역</div>
              <span class="badge text-bg-light">translate</span>
            </div>
            <p class="ai-feature-desc" style="line-height:1.6;">
              한국어 ↔ 영어 번역을 지원합니다. (방향 선택)
            </p>
            <button class="btn btn-outline-primary rounded-4 ai-quick-select"
                    type="button"
                    data-ai-service="translate">
              이 기능으로 시작
            </button>
          </div>
        </div>
      </div>

      <div class="col-12 col-md-6 col-lg-6">
        <div class="card h-100 rounded-4 border-0 shadow-sm ai-feature-card">
          <div class="card-body p-4 ai-feature-card">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <div class="fw-bold">🧾 문장 요약</div>
              <span class="badge text-bg-light">summary</span>
            </div>
            <p class="ai-feature-desc" style="line-height:1.6;">
              긴 문장을 핵심 위주로 간단히 요약합니다.
            </p>
            <button class="btn btn-outline-primary rounded-4 ai-quick-select"
                    type="button"
                    data-ai-service="summary">
              이 기능으로 시작
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 실행 콘솔 -->
    <div id="ai-console" class="card rounded-4 border-0 shadow-sm ai-feature-card ai-console">
      <div class="card-body p-4 p-lg-5 ai-feature-card">

        <div class="d-flex flex-column flex-lg-row align-items-lg-end justify-content-between gap-3 mb-3">
          <div>
            <h2 class="h5 fw-bold mb-1">실행 콘솔</h2>
            <div class="text-muted small">기능 선택 → 입력 → 실행 결과 확인</div>
          </div>
          <div class="text-muted small">
            JS: <code>static/js/ai_page.js</code>
          </div>
        </div>

        <!-- 기능 선택 -->
        <div class="mb-3">
          <label for="ai-service-select" class="form-label fw-semibold">AI 기능 선택</label>
          <select id="ai-service-select" class="form-select">
            <option value="sentiment">감정 분석</option>
            <option value="entities">개체 분석</option>
            <option value="qa">질의 응답</option>
            <option value="translate">번역</option>
            <option value="summary">문장 요약</option>
          </select>

          <div id="ai-service-help" class="form-text text-muted mt-1">
            감정 분석: 문장의 감정(긍정/부정 등)을 분석합니다.
          </div>
        </div>

        <!-- 번역 옵션 (기본 숨김) -->
        <div id="translate-options" class="mb-3" style="display:none;">
          <label for="ai-translate-direction" class="form-label me-2">번역 방향</label>
          <select id="ai-translate-direction" class="form-select form-select-sm d-inline-block w-auto">
            <option value="ko-en">한국어 → 영어</option>
            <option value="en-ko">영어 → 한국어</option>
          </select>
          <div class="form-text text-muted">
            * 번역 기능 선택 시에만 의미가 있습니다.
          </div>
        </div>

        <!-- QA 옵션 (기본 숨김) -->
        <div id="qa-options" class="mb-3" style="display:none;">
          <label for="ai-qa-context" class="form-label fw-semibold">지문(Context)</label>
          <textarea id="ai-qa-context"
                    class="form-control"
                    rows="4"
                    placeholder="질의응답(qa)은 지문이 필수입니다. 여기에 지문을 입력하세요."></textarea>
          <div class="form-text text-muted">
            * qa 선택 시: text(질문) + options.context(지문)이 모두 필요합니다.
          </div>
        </div>

        <!-- 입력 -->
        <div class="mb-3">
          <label for="ai-input-text" class="form-label fw-semibold">입력 텍스트</label>
          <textarea id="ai-input-text"
                    class="form-control"
                    rows="4"
                    placeholder="분석하거나 질문할 문장을 입력하세요."></textarea>
        </div>

        <!-- 버튼 -->
        <div class="d-flex flex-wrap gap-2 mb-3">
          <button id="ai-run-btn" class="btn btn-primary rounded-4 px-4" type="button">실행</button>
          <button id="ai-clear-btn" class="btn btn-outline-secondary rounded-4 px-4" type="button">초기화</button>
        </div>

        <!-- 결과 -->
        <div id="ai-chat-box"
             class="border rounded-4 p-3 ai-chat-box"
             style="min-height:160px; max-height:420px; overflow-y:auto;">
          <div class="text-muted small">
            아직 결과가 없습니다. 텍스트를 입력하고 <strong>실행</strong>을 눌러보세요.
          </div>
        </div>

      </div>
    </div>

  </div>
</section>
{% endblock %}

{% block extra_js %}
  <script src="{{ url_for('static', filename='js/ai_page.js') }}"></script>
  <script src="{{ url_for('static', filename='js/auth_ui.js') }}"></script>
{% endblock %}
{% block extra_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/ai.css') }}">
{% endblock %}
```