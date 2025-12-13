

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
          {# ✅ 전역 네비를 base에서 제공 (각 페이지는 header 블록을 되도록 쓰지 않음) #}
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

    <!-- ✅ 전역: 준비중 모달 (페이지 어디서든 호출 가능) -->
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

    <!-- ✅ 전역 JS (준비중 링크를 모달로 연결) -->
    <script src="{{ url_for('static', filename='js/app_ui.js') }}"></script>

    {% block extra_js %}{% endblock %}
  </body>
</html>
```

# FILE: belong/web/main/templates/navbar.html
```{# templates/navbar.html #}
<nav class="navbar navbar-expand-lg navbar-dark" data-component="navbar">
  <div class="container">

    <!-- 브랜드: 홈 -->
    <a class="navbar-brand d-flex align-items-center fw-bold" href="{{ url_for('web.index') }}">
      <img
        src="{{ url_for('static', filename='image/logo.png') }}"
        alt="Belong Logo"
        style="height:40px; border-radius:8px; margin-right:10px;"
      >
      <span style="font-size:22px;">Belong</span>
    </a>

    <!-- 모바일 토글 -->
    <button class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarNav"
            aria-controls="navbarNav"
            aria-expanded="false"
            aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>

    <!-- 메뉴 -->
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto align-items-lg-center gap-lg-2">

        <!-- 1) 대시보드 -->
        <li class="nav-item">
          <a class="nav-link" href="{{ url_for('web.dashboard') }}">대시보드</a>
        </li>

        <!-- 2) AI 챗봇(5기능 허브로 이동) -->
        <li class="nav-item">
          <a class="nav-link" href="{{ url_for('web.ai_home') }}">AI 챗봇</a>
        </li>
        <!-- 3) AI Agent (준비중) -->
        <li class="nav-item">
          <a class="nav-link is-coming-soon"
             href="#"
             data-coming-soon="agent">
            AI Agent <span class="badge text-bg-secondary ms-1">준비중</span>
          </a>
        </li>
        <!-- 4) Agentic AI (준비중) -->
        <li class="nav-item">
          <a class="nav-link is-coming-soon"
             href="#"
             data-coming-soon="agentic">
            Agentic AI <span class="badge text-bg-secondary ms-1">준비중</span>
          </a>
        </li>
        <!-- 로그인/회원가입/유저 -->
        <li class="nav-item" id="nav-login">
          <a class="nav-link" href="{{ url_for('web.login') }}">로그인</a>
        </li>

        <li class="nav-item" id="nav-signup">
          <a class="nav-link" href="{{ url_for('web.signup') }}">회원가입</a>
        </li>

        <li class="nav-item dropdown d-none" id="nav-user">
          <a class="nav-link dropdown-toggle"
             href="#"
             id="userDropdown"
             role="button"
             data-bs-toggle="dropdown"
             aria-expanded="false">
            <span id="nav-username">사용자</span>
          </a>

          <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
            <li>
              <a class="dropdown-item" href="{{ url_for('web.logout') }}" id="logout-btn">로그아웃</a>
            </li>
          </ul>
        </li>

      </ul>
    </div>
  </div>
</nav>
```

# FILE: belong/web/main/templates/index.html
```{# templates/index.html #}
{% extends "base.html" %}

{% block title %}Belong - 데이터 기반 케어 플랫폼{% endblock %}

{% block page_id %}home{% endblock %}
{% block body_class %}home-page{% endblock %}

{% block extra_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/home.css') }}">
{% endblock %}

{% block content %}

<!-- HERO -->
<section class="hero-section">
  <div class="page-container">
    <div class="hero-grid">

      <!-- Left -->
      <div>
        <span class="hero-eyebrow">BELONG PLATFORM</span>

        <h1 class="hero-title">
          대시보드와 AI로<br class="d-none d-md-block">
          더 빠르게, 더 정확하게.
        </h1>

        <p class="hero-subtitle">
          Belong은 <strong>대시보드</strong>와 <strong>AI 챗봇 서비스(5기능)</strong>를 중심으로 운영됩니다.
          <br class="d-none d-md-block">
          <strong>AI Agent</strong>와 <strong>Agentic AI</strong>는 확장을 위한 UI 구조만 먼저 준비해둡니다.
        </p>

        <div class="d-flex flex-wrap gap-2">
          <a class="btn btn-primary btn-lg rounded-4 px-4" href="{{ url_for('web.dashboard') }}">
            대시보드 시작
          </a>

          <a class="btn btn-outline-primary btn-lg rounded-4 px-4" href="{{ url_for('web.ai_home') }}">
            AI 챗봇 열기
          </a>

          <button class="btn btn-outline-secondary btn-lg rounded-4 px-4" data-coming-soon="agent">
            AI Agent
          </button>

          <button class="btn btn-outline-secondary btn-lg rounded-4 px-4" data-coming-soon="agentic">
            Agentic AI
          </button>
        </div>

        <div class="hero-meta">
          빠른 이동:
          <a href="#features">주요 기능</a>
          ·
          <a href="#how">사용 방법</a>
          ·
          <a href="#roadmap">확장 로드맵</a>
        </div>
      </div>

      <!-- Right -->
      <div class="hero-visual">
        <div class="card hero-visual-card border-0">
          <div class="hero-visual-media">
            <img
              class="hero-image"
              src="{{ url_for('static', filename='image/region.jpg') }}"
              alt="Belong Visual"
            >
          </div>

          <div class="hero-visual-text">
            <div class="hero-visual-title">현재 구현된 핵심</div>
            <div class="hero-visual-desc">
              ① 대시보드(데이터 탐색) · ② AI 챗봇(번역/감정/요약/Q&A/객체)
              <br>
              → UI 구조를 먼저 안정화하고, 이후 AI Agent 확장을 수용합니다.
            </div>

            <hr class="my-3">

            <div class="d-grid gap-2">
              <a class="btn btn-outline-primary rounded-4" href="{{ url_for('web.dashboard') }}">
                대시보드로 이동
              </a>
              <a class="btn btn-outline-primary rounded-4" href="{{ url_for('web.ai_home') }}">
                AI 챗봇으로 이동
              </a>
              <button class="btn btn-light rounded-4" disabled>
                AI Agent (준비중)
              </button>
              <button class="btn btn-light rounded-4" disabled>
                Agentic AI (준비중)
              </button>
            </div>

            <div class="d-flex gap-2 mt-3">
              <a class="btn btn-light w-50 rounded-4" href="{{ url_for('web.login') }}">
                로그인
              </a>
              <a class="btn btn-light w-50 rounded-4" href="{{ url_for('web.signup') }}">
                회원가입
              </a>
            </div>

          </div>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- FEATURES -->
<section id="features" class="services-section">
  <div class="page-container">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">주요 기능</h2>
      <p class="text-muted mb-0">
        홈/네비게이션은 <strong>4개의 제품 기능</strong> 기준으로 통일합니다.
      </p>
    </div>

    <div class="row g-3">

      <!-- Dashboard -->
      <div class="col-12 col-md-6 col-lg-3">
        <div class="card h-100 rounded-4 shadow-sm border-0">
          <div class="card-body p-4 d-flex flex-column">
            <h5 class="feature-card-title">대시보드</h5>
            <p class="feature-card-desc">
              데이터 흐름을 빠르게 파악하고, 비교/추세 중심으로 탐색합니다.
            </p>
            <div class="mt-auto">
              <a class="btn btn-primary rounded-4" href="{{ url_for('web.dashboard') }}">
                이동
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Chatbot -->
      <div class="col-12 col-md-6 col-lg-3">
        <div class="card h-100 rounded-4 shadow-sm border-0">
          <div class="card-body p-4 d-flex flex-column">
            <h5 class="feature-card-title">AI 챗봇 서비스</h5>
            <p class="feature-card-desc">
              번역 / 감정분석 / 요약 / 질의응답 / 객체분석 등 5가지 기능을 한 곳에서 제공합니다.
            </p>
            <div class="mt-auto">
              <a class="btn btn-outline-primary rounded-4" href="{{ url_for('web.ai_home') }}">
                이동
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Agent -->
      <div class="col-12 col-md-6 col-lg-3">
        <div class="card h-100 rounded-4 shadow-sm border-0">
          <div class="card-body p-4 d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between">
              <h5 class="feature-card-title mb-0">AI Agent</h5>
              <span class="badge text-bg-secondary">준비중</span>
            </div>
            <p class="feature-card-desc mt-2">
              목표 중심으로 작업을 분해하고, 필요한 도구를 호출해 결과를 만들어내는 에이전트 기능.
            </p>
            <div class="mt-auto">
              <button class="btn btn-outline-secondary rounded-4 w-100" data-coming-soon="agent">
                준비중
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Agentic AI -->
      <div class="col-12 col-md-6 col-lg-3">
        <div class="card h-100 rounded-4 shadow-sm border-0">
          <div class="card-body p-4 d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between">
              <h5 class="feature-card-title mb-0">Agentic AI</h5>
              <span class="badge text-bg-secondary">준비중</span>
            </div>
            <p class="feature-card-desc mt-2">
              멀티 에이전트/워크플로우 기반으로 장기 목표를 수행하는 형태의 기능.
            </p>
            <div class="mt-auto">
              <button class="btn btn-outline-secondary rounded-4 w-100" data-coming-soon="agentic">
                준비중
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- HOW TO -->
<section id="how" class="how-section">
  <div class="page-container">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">사용 방법</h2>
      <p class="text-muted mb-0">현재 구현된 기능 기준으로, 가장 자연스러운 사용 흐름입니다.</p>
    </div>

    <div class="row g-3">
      <div class="col-12 col-lg-6">
        <div class="card h-100 rounded-4 border-0 shadow-sm">
          <div class="card-body p-4">
            <div class="how-card-title">1) 대시보드로 데이터 흐름 파악</div>
            <div class="how-card-desc">
              연도/지역을 선택하고 그래프/비교를 통해 전체 흐름을 확인합니다.
            </div>
            <div class="mt-3">
              <a href="{{ url_for('web.dashboard') }}">대시보드 열기 →</a>
            </div>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-6">
        <div class="card h-100 rounded-4 border-0 shadow-sm">
          <div class="card-body p-4">
            <div class="how-card-title">2) AI 챗봇으로 해석/보조 작업 수행</div>
            <div class="how-card-desc">
              번역/감정/요약/Q&A/객체분석 등 필요한 AI 기능을 선택해 빠르게 처리합니다.
            </div>
            <div class="mt-3">
              <a href="{{ url_for('web.ai_home') }}">AI 챗봇 열기 →</a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-4 small text-muted">
      * AI Agent / Agentic AI는 “준비중” 상태로 UI에만 노출되며, 구현 완료 시 이 흐름에 자연스럽게 확장됩니다.
    </div>
  </div>
</section>

<!-- ROADMAP -->
<section id="roadmap" class="roadmap-section">
  <div class="page-container">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">확장 로드맵(UI 관점)</h2>
      <p class="text-muted mb-0">
        지금은 구현된 기능(대시보드/AI챗봇)을 안정화하고, 확장 기능을 “붙일 수 있는 구조”를 유지합니다.
      </p>
    </div>

    <div class="row g-3">
      <div class="col-12 col-lg-4">
        <div class="card h-100 rounded-4 border-0 shadow-sm">
          <div class="card-body p-4">
            <div class="roadmap-title">Phase 1: UI 구조 안정화</div>
            <div class="roadmap-desc">
              공통 컴포넌트(네비/레이아웃) 단일화, 전역/페이지 CSS 분리,
              참조(엔드포인트/ID/클래스) 규칙 고정.
            </div>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-4">
        <div class="card h-100 rounded-4 border-0 shadow-sm">
          <div class="card-body p-4">
            <div class="roadmap-title">Phase 2: AI Agent UI 스켈레톤</div>
            <div class="roadmap-desc">
              “준비중” 탭에 실제 페이지를 연결하고, 상태/로그/결과를 보여주는 레이아웃부터 확정.
            </div>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-4">
        <div class="card h-100 rounded-4 border-0 shadow-sm">
          <div class="card-body p-4">
            <div class="roadmap-title">Phase 3: Agentic AI 확장</div>
            <div class="roadmap-desc">
              워크플로우/멀티에이전트 시각화(실행흐름, 도구 호출, 결과물)를 대시보드와 연결할 수 있는 구조로 확장.
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</section>

{% endblock %}
```

# FILE: belong/web/main/templates/dashboard.html
```{# templates/dashboard.html #}
{% extends "base.html" %}

{% block title %}고독사 리스크 대시보드 - Belong{% endblock %}

{% block extra_css %}
  {# 대시보드 전용 CSS #}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
{% endblock %}

{% block header %}
  <div class="page-container">
    {% include "navbar.html" %}
  </div>
{% endblock %}

{% block content %}
<section class="section dashboard-section py-4">
  <div class="page-container">
    <div class="dashboard-layout row g-3">

      <!-- ================= 좌측: 필터 / 구×연도 그리드 ================= -->
      <aside class="dashboard-sidebar col-12 col-lg-3">
        <div class="card card-soft h-100">
          <div class="card-body">
            <h5 class="fw-bold mb-2">대시보드</h5>
            <p class="text-muted small mb-3">
              연도 구간과 지역(최대 2개)을 선택하면 오른쪽 그래프가 갱신됩니다.
            </p>

            <!-- 연도 범위 -->
            <div class="mb-3">
              <label class="form-label form-label-sm mb-1">연도 범위</label>
              <div class="d-flex gap-2">
                <select id="year-start" class="form-select form-select-sm"></select>
                <select id="year-end" class="form-select form-select-sm"></select>
              </div>
              <div class="form-text small">
                기본값: 2017 ~ 2023 (URL 파라미터로 변경 가능)
              </div>
            </div>

            <!-- 지역 선택 -->
            <div class="mb-3">
              <label class="form-label form-label-sm mb-1">지역 선택 (최대 2개)</label>
              <div id="control-region-checkboxes" class="region-checkbox-list">
                <!-- JS에서 체크박스 생성 -->
              </div>
              <div class="form-text small">
                기본값: 강남구, 종로구
              </div>
            </div>

            <!-- 적용 버튼 -->
            <div class="d-grid mb-3">
              <button id="btn-apply-dashboard" class="btn btn-primary btn-sm">
                선택 완료
              </button>
            </div>

            <!-- 구×연도 그리드 -->
            <div class="mt-3">
              <h6 class="small fw-semibold mb-2">구 × 연도 (선택 범위)</h6>
              <div id="year-region-grid" class="year-region-grid-wrap">
                {# JS에서 테이블 렌더링 #}
              </div>
              <div class="form-text small mt-1">
                링크 공유/새로고침 시 선택 상태가 유지되도록 URL에 저장됩니다.
              </div>
            </div>

          </div>
        </div>
      </aside>

      <!-- ================= 우측: 그래프 영역 ================= -->
      <div class="dashboard-content col-12 col-lg-9">
        <div class="row g-3">

          <!-- ===== 슬롯 1 ===== -->
          <div class="col-12 col-xl-6">
            <div class="card card-soft h-100">
              <div class="card-body">
                <div class="slot-header">
                  <h5 class="slot-title" id="region-title-1">강남구</h5>

                  {# ✅ 지역 상세(Region) 페이지는 현재 서비스 범위에서 제외 → 링크 제거 #}
                  <button
                    class="btn btn-outline-secondary btn-sm"
                    type="button"
                    disabled
                    title="준비중(현재는 대시보드/AI 챗봇 중심으로 운영)"
                  >
                    상세
                  </button>
                </div>

                <div class="row g-3">
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">독거노인 추세</h6>
                    <div class="chart-wrapper">
                      <canvas id="trend-elderly-1"></canvas>
                    </div>
                  </div>
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">고독사 추세</h6>
                    <div class="chart-wrapper">
                      <canvas id="trend-lonely-1"></canvas>
                    </div>
                  </div>
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">독거노인 5년 예측</h6>
                    <div class="chart-wrapper">
                      <canvas id="forecast-elderly-1"></canvas>
                    </div>
                  </div>
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">고독사 5년 예측</h6>
                    <div class="chart-wrapper">
                      <canvas id="forecast-lonely-1"></canvas>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
          <!-- ===== /슬롯 1 ===== -->

          <!-- ===== 슬롯 2 ===== -->
          <div class="col-12 col-xl-6" id="graph-column-2">
            <div class="card card-soft h-100">
              <div class="card-body">
                <div class="slot-header">
                  <h5 class="slot-title" id="region-title-2">종로구</h5>

                  {# ✅ 지역 상세(Region) 페이지는 현재 서비스 범위에서 제외 → 링크 제거 #}
                  <button
                    class="btn btn-outline-secondary btn-sm"
                    type="button"
                    disabled
                    title="준비중(현재는 대시보드/AI 챗봇 중심으로 운영)"
                  >
                    상세
                  </button>
                </div>

                <div class="row g-3">
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">독거노인 추세</h6>
                    <div class="chart-wrapper">
                      <canvas id="trend-elderly-2"></canvas>
                    </div>
                  </div>
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">고독사 추세</h6>
                    <div class="chart-wrapper">
                      <canvas id="trend-lonely-2"></canvas>
                    </div>
                  </div>
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">독거노인 5년 예측</h6>
                    <div class="chart-wrapper">
                      <canvas id="forecast-elderly-2"></canvas>
                    </div>
                  </div>
                  <div class="col-12 col-md-6">
                    <h6 class="chart-title">고독사 5년 예측</h6>
                    <div class="chart-wrapper">
                      <canvas id="forecast-lonely-2"></canvas>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
          <!-- ===== /슬롯 2 ===== -->

        </div>
      </div>

    </div>
  </div>
</section>
{% endblock %}

{% block extra_js %}
  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <!-- 대시보드 JS -->
  <script src="{{ url_for('static', filename='charts/dashboard.js') }}"></script>
{% endblock %}
```

# FILE: belong/web/main/templates/ai_tool.html
```{# templates/ai_tool.html (프로젝트 경로에 맞게) #}
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
              질문을 입력하면 답변을 생성합니다.
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

        <!-- 번역 옵션 -->
        <div id="translate-options" class="mb-3">
          <label for="ai-translate-direction" class="form-label me-2">번역 방향</label>
          <select id="ai-translate-direction" class="form-select form-select-sm d-inline-block w-auto">
            <option value="ko-en">한국어 → 영어</option>
            <option value="en-ko">영어 → 한국어</option>
          </select>
          <div class="form-text text-muted">
            * 번역 기능 선택 시에만 의미가 있습니다.
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
{% endblock %}
{% block extra_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/ai.css') }}">
{% endblock %}
```

# FILE: belong/templates/layout.html
```<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
    <a class="navbar-brand" href="/">Belong</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">
            <li class="nav-item"><a class="nav-link" href="/">홈</a></li>
            <li class="nav-item"><a class="nav-link" href="/dashboard">대시보드</a></li>
            <li class="nav-item"><a class="nav-link" href="/region">지역 예측</a></li>
            <li class="nav-item"><a class="nav-link" href="/correlation">상관관계 분석</a></li>
        </ul>
    </div>
</nav>```

# FILE: belong/templates/macros.html
``````

# FILE: belong/static/js/navbar.js
```// static/js/navbar.js
document.addEventListener("DOMContentLoaded", () => {
  const navLogin = document.getElementById("nav-login");
  const navSignup = document.getElementById("nav-signup");
  const navUser = document.getElementById("nav-user");
  const navUsername = document.getElementById("nav-username");
  const logoutBtn = document.getElementById("logout-btn");

  let user = null;
  try {
    user = JSON.parse(localStorage.getItem("belong_user") || "null");
  } catch (e) {
    user = null;
  }

  if (user && user.username) {
    navLogin?.classList.add("d-none");
    navSignup?.classList.add("d-none");
    navUser?.classList.remove("d-none");
    if (navUsername) navUsername.textContent = user.username;

    logoutBtn?.addEventListener("click", () => {
      localStorage.removeItem("belong_user");
    });
  } else {
    navLogin?.classList.remove("d-none");
    navSignup?.classList.remove("d-none");
    navUser?.classList.add("d-none");
  }
});
```

# FILE: belong/static/js/ai_page.js
```// static/js/ai_page.js
document.addEventListener("DOMContentLoaded", () => {
  const serviceSelect = document.getElementById("ai-service-select");
  const inputEl       = document.getElementById("ai-input-text");
  const chatBox       = document.getElementById("ai-chat-box");
  const runBtn        = document.getElementById("ai-run-btn");
  const clearBtn      = document.getElementById("ai-clear-btn");
  const directionEl   = document.getElementById("ai-translate-direction");
  const translateOpts = document.getElementById("translate-options");
  const serviceHelp   = document.getElementById("ai-service-help");

  if (!serviceSelect || !inputEl || !chatBox || !runBtn) return;

  // ---- 서비스별 설명 문구 ----
  const helpTexts = {
    sentiment: "감정 분석: 문장의 감정(긍정/부정 등)을 분석합니다.",
    entities:  "개체 분석: 문장에서 사람, 기관, 장소 등을 추출합니다.",
    qa:        "질의 응답: 주어진 텍스트를 기반으로 질문에 답변합니다.",
    translate: "번역: 한국어↔영어 번역을 수행합니다.",
    summary:   "문장 요약: 긴 문장을 짧게 요약합니다.",
  };

  function updateServiceHelp() {
    const key = serviceSelect.value;
    if (serviceHelp) {
      serviceHelp.textContent = helpTexts[key] || "";
    }
  }

  function updateTranslateOptions() {
    const svc = serviceSelect.value;
    if (translateOpts) {
      translateOpts.style.display = (svc === "translate") ? "block" : "none";
    }
  }

  // 서비스 바뀔 때 옵션 표시/숨기기 + 설명 업데이트
  serviceSelect.addEventListener("change", () => {
    updateTranslateOptions();
    updateServiceHelp();
  });

  // 초기 상태 반영
  updateServiceHelp();
  updateTranslateOptions();

  // ✅ 빠른 선택 카드(템플릿 인라인 JS 제거 → 여기서 처리)
  document.querySelectorAll(".ai-quick-select").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = btn.getAttribute("data-ai-service");
      if (!v) return;

      serviceSelect.value = v;
      serviceSelect.dispatchEvent(new Event("change", { bubbles: true }));

      // 사용자가 바로 입력할 수 있게 포커스
      inputEl.focus();

      // 콘솔로 스크롤(부드럽게)
      const consoleEl = document.getElementById("ai-console");
      if (consoleEl) {
        consoleEl.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  // ---- 채팅 말풍선 추가 함수 ----
  function appendMessage(role, text) {
    const wrap = document.createElement("div");
    wrap.classList.add("mb-2", "d-flex");
    wrap.classList.add(role === "user" ? "justify-content-end" : "justify-content-start");

    const bubble = document.createElement("div");
    bubble.classList.add("px-3", "py-2", "rounded-3", "small");

    if (role === "user") {
      bubble.classList.add("bg-primary", "text-white");
    } else {
      bubble.classList.add("bg-light");
    }

    bubble.textContent = text;
    wrap.appendChild(bubble);
    chatBox.appendChild(wrap);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // ---- 결과 포맷터: 서비스별로 보기 좋게 변환 ----
  function formatResult(service, result) {
    if (result == null) return "결과가 비어 있습니다.";

    if (service === "sentiment") {
      if (typeof result === "object" && !Array.isArray(result)) {
        const label = result.label || "라벨 미상";
        const score = typeof result.score === "number" ? (result.score * 100).toFixed(1) + "%" : "";
        return score ? `감정 분석 결과: ${label} (${score})` : `감정 분석 결과: ${label}`;
      }
      if (Array.isArray(result)) {
        if (result.length === 0) return "감정 분석 결과가 없습니다.";
        const lines = result.map((item, idx) => {
          const label = item.label || item.class || item.prediction || "라벨 미상";
          const score = typeof item.score === "number" ? (item.score * 100).toFixed(1) + "%" : "";
          const prefix = result.length > 1 ? `${idx + 1}. ` : "- ";
          return score ? `${prefix}${label} (${score})` : `${prefix}${label}`;
        });
        return "감정 분석 결과:\n" + lines.join("\n");
      }
      return typeof result === "string" ? result : JSON.stringify(result, null, 2);
    }

    if (service === "entities") {
      let entities = [];
      if (Array.isArray(result)) entities = result;
      else if (result && Array.isArray(result.entities)) entities = result.entities;

      if (entities.length === 0) return "인식된 개체가 없습니다.";

      function mapEntityType(t) {
        if (!t) return "타입 미상";
        const up = String(t).toUpperCase();
        if (up.includes("PER"))  return "사람(PER)";
        if (up.includes("ORG"))  return "기관/회사(ORG)";
        if (up.includes("LOC"))  return "장소(LOC)";
        if (up.includes("MISC")) return "기타(MISC)";
        return t;
      }

      const lines = entities.map((ent, idx) => {
        const word  = ent.text || ent.word || ent.token || "";
        const type  = mapEntityType(ent.entity || ent.entity_group || ent.label);
        const score = typeof ent.score === "number" ? (ent.score * 100).toFixed(1) + "%" : "";
        let base = `${idx + 1}. "${word}"`;
        const meta = [];
        if (type)  meta.push(`타입: ${type}`);
        if (score) meta.push(`신뢰도: ${score}`);
        if (meta.length > 0) base += ` (${meta.join(", ")})`;
        return base;
      });

      return "인식된 개체들:\n" + lines.join("\n");
    }

    if (service === "qa") {
      if (result && typeof result === "object") {
        if (result.answer) {
          const score = typeof result.score === "number" ? (result.score * 100).toFixed(1) + "%" : null;
          return score ? `답변: ${result.answer}\n(신뢰도: ${score})` : `답변: ${result.answer}`;
        }
        return JSON.stringify(result, null, 2);
      }
      return typeof result === "string" ? result : JSON.stringify(result, null, 2);
    }

    if (service === "summary") {
      if (result && typeof result === "object" && result.summary) return `요약:\n${result.summary}`;
      return typeof result === "string" ? result : JSON.stringify(result, null, 2);
    }

    if (service === "translate") {
      if (result && typeof result === "object" && result.translation) {
        const dir = result.direction === "en-ko" ? "영어 → 한국어" : "한국어 → 영어";
        return `번역(${dir}):\n${result.translation}`;
      }
      return typeof result === "string" ? result : JSON.stringify(result, null, 2);
    }

    return typeof result === "string" ? result : JSON.stringify(result, null, 2);
  }

  // ✅ 서비스 → API 엔드포인트 맵 (if-else 제거: 실수↓)
  const ENDPOINTS = {
    sentiment: "/api/ai/sentiment",
    entities:  "/api/ai/entities",
    qa:        "/api/ai/qa",
    summary:   "/api/ai/summary",
    translate: "/api/ai/translate",
  };

  runBtn.addEventListener("click", async () => {
    const text = (inputEl.value || "").trim();
    if (!text) {
      appendMessage("assistant", "텍스트를 입력해주세요.");
      return;
    }

    const service = serviceSelect.value;
    const url = ENDPOINTS[service];

    if (!url) {
      appendMessage("assistant", `알 수 없는 서비스: ${service}`);
      return;
    }

    appendMessage("user", text);
    inputEl.value = "";

    const options = {};
    if (service === "translate" && directionEl) {
      options.direction = directionEl.value; // "ko-en" or "en-ko"
    }

    const payload = { text, options };

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || data.ok === false) {
        const msg = data.error || `요청 실패 (${res.status})`;
        appendMessage("assistant", msg);
        return;
      }

      const formatted = formatResult(service, data.result);
      appendMessage("assistant", formatted);
    } catch (err) {
      console.error(err);
      appendMessage("assistant", "서버와 통신 중 오류가 발생했습니다.");
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      chatBox.innerHTML = '<div class="text-muted small">대화 내역이 초기화되었습니다.</div>';
    });
  }
});
```

# FILE: belong/static/js/app_ui.js
```// static/js/app_ui.js
document.addEventListener("DOMContentLoaded", () => {
  const modalEl = document.getElementById("comingSoonModal");
  if (!modalEl || !window.bootstrap) return;

  const titleEl = document.getElementById("comingSoonTitle");
  const bodyEl  = document.getElementById("comingSoonBody");

  const modal = new bootstrap.Modal(modalEl);

  const COPY = {
    agent: {
      title: "AI Agent (준비중)",
      body: "AI Agent는 목표를 받으면 작업을 분해하고 도구를 호출해 결과를 만들어내는 기능입니다. 현재는 UI 구조만 준비해두었고 다음 단계에서 연결됩니다."
    },
    agentic: {
      title: "Agentic AI (준비중)",
      body: "Agentic AI는 멀티 에이전트/워크플로우 기반으로 장기 목표를 수행하는 기능입니다. 현재는 UI 구조만 준비해두었고 다음 단계에서 연결됩니다."
    }
  };

  // data-coming-soon 속성이 붙은 모든 요소가 대상
  document.querySelectorAll("[data-coming-soon]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const key = el.getAttribute("data-coming-soon");
      const copy = COPY[key] || { title: "준비중", body: "현재 준비 중인 기능입니다." };

      if (titleEl) titleEl.textContent = copy.title;
      if (bodyEl) bodyEl.textContent = copy.body;

      modal.show();
    });
  });
});
```

# FILE: belong/static/charts/dashboard.js
```// static/charts/dashboard.js
// =======================================
// Belong 대시보드 v2 (+ 구×연도 그리드)
// - 좌측: 연도 / 지역 선택 (최대 2개)
// - 우측: 각 지역별 4개 그래프
//   1) 독거노인(노인 인구) 추세
//   2) 고독사 추세
//   3) 독거노인(노인 인구) 5년 예측
//   4) 고독사 5년 예측
// - 추가: 선택된 "구 × 연도"를 보여주는 그리드
// - URL 상태 동기화: ?from=2017&to=2023&r=강남구,종로구
// =======================================

// ----- 설정 -----
const YEAR_MIN = 2017;
const YEAR_MAX = 2035;

// 서울 25개 구
const SEOUL_GU_LIST = [
  "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구",
  "동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구",
  "용산구","은평구","종로구","중구","중랑구",
];

// 슬롯별 기본 컬러(원래 코드 스타일 유지)
const SLOT_COLORS = {
  1: {
    elderlyTrend: "#2563EB",
    lonelyTrend: "#E11D48",
    elderlyForecast: "#60A5FA",
    lonelyForecast: "#FB7185",
  },
  2: {
    elderlyTrend: "#16A34A",
    lonelyTrend: "#F59E0B",
    elderlyForecast: "#86EFAC",
    lonelyForecast: "#FCD34D",
  },
};

// ----- 상태 -----
let selectedStartYear = 2017;
let selectedEndYear = 2023;
let selectedRegions = ["강남구", "종로구"];

// 차트 인스턴스 저장(캔버스 id별)
const chartStore = {};

// ------------------------------
// 유틸
// ------------------------------
function clampYear(y) {
  if (!Number.isFinite(y)) return YEAR_MIN;
  return Math.min(YEAR_MAX, Math.max(YEAR_MIN, y));
}

function readDashboardStateFromUrl() {
  const qs = new URLSearchParams(location.search);

  const from = parseInt(qs.get("from"), 10);
  const to = parseInt(qs.get("to"), 10);
  const r = qs.get("r"); // "강남구,종로구"

  if (!Number.isNaN(from)) selectedStartYear = clampYear(from);
  if (!Number.isNaN(to)) selectedEndYear = clampYear(to);

  if (r) {
    const arr = r
      .split(",")
      .map((s) => decodeURIComponent(s.trim()))
      .filter(Boolean);

    // 최대 2개까지만
    if (arr.length >= 1) selectedRegions = arr.slice(0, 2);
  }
}

function writeDashboardStateToUrl() {
  const qs = new URLSearchParams();
  qs.set("from", String(selectedStartYear));
  qs.set("to", String(selectedEndYear));
  qs.set("r", selectedRegions.map(encodeURIComponent).join(","));
  history.replaceState(null, "", `${location.pathname}?${qs.toString()}`);
}

async function fetchJson(url) {
  const res = await fetch(url);
  let json;
  try {
    json = await res.json();
  } catch (e) {
    console.error("JSON 파싱 실패:", url, e);
    throw new Error("서버 응답을 해석할 수 없습니다.");
  }
  if (!res.ok || (json.status && String(json.status).toLowerCase() === "error")) {
    const msg = json.message || `요청 실패 (${res.status})`;
    throw new Error(msg);
  }
  return json;
}

function extractYear(row) {
  const y = Number(row?.year);
  return Number.isFinite(y) ? y : null;
}

function extractValue(row) {
  if (!row || typeof row !== "object") return 0;

  const keys = [
    "value",
    "elderly_population",
    "lonely_death",
    "lonely_deaths",
    "count",
    "population",
    "predicted_value",
    "y",
  ];

  for (const k of keys) {
    if (row[k] === 0) return 0;
    if (row[k] != null && row[k] !== "") {
      const n = Number(row[k]);
      if (Number.isFinite(n)) return n;
    }
  }
  return 0;
}

// ------------------------------
// 차트 생성(라인 차트)
// ------------------------------
function createLineChart(canvasId, labels, data, color, label, dashed = false, fill = false) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (typeof Chart === "undefined") {
    console.error("[dashboard] Chart.js가 로드되지 않았습니다.");
    return;
  }

  const ctx = canvas.getContext("2d");

  if (chartStore[canvasId]) {
    chartStore[canvasId].destroy();
  }

  chartStore[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label,
          data,
          borderColor: color,
          backgroundColor: fill ? `${color}33` : `${color}22`,
          borderWidth: 2,
          fill: fill,
          tension: 0.35,
          pointRadius: 3,
          pointHoverRadius: 4,
          spanGaps: true,
          borderDash: dashed ? [6, 6] : [],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: { mode: "index", intersect: false },
      },
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          ticks: {
            maxTicksLimit: 6,
          },
        },
        y: {
          ticks: {
            maxTicksLimit: 5,
          },
        },
      },
    },
  });
}

// ------------------------------
// 구 × 연도 그리드 렌더
// ------------------------------
function renderYearRegionGrid() {
  const container = document.getElementById("year-region-grid");
  if (!container) return;

  container.innerHTML = "";

  const years = [];
  for (let y = selectedStartYear; y <= selectedEndYear; y++) years.push(y);

  // 테이블 생성
  const table = document.createElement("table");
  table.className = "table table-sm table-bordered align-middle mb-0";

  // 헤더
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  const th0 = document.createElement("th");
  th0.textContent = "연도\\지역";
  trh.appendChild(th0);

  selectedRegions.forEach((region) => {
    const th = document.createElement("th");
    th.textContent = region;
    trh.appendChild(th);
  });

  thead.appendChild(trh);
  table.appendChild(thead);

  // 바디
  const tbody = document.createElement("tbody");
  years.forEach((year) => {
    const tr = document.createElement("tr");

    const tdYear = document.createElement("td");
    tdYear.textContent = year;
    tr.appendChild(tdYear);

    selectedRegions.forEach((region) => {
      const td = document.createElement("td");
      td.textContent = "●";
      td.title = `${region} - ${year}`;
      td.className = "year-region-grid-cell";
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  container.appendChild(table);
}

// ------------------------------
// 초기화
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
  // ✅ URL 상태 먼저 반영
  readDashboardStateFromUrl();

  initYearSelects();
  initRegionCheckboxes();

  document.getElementById("btn-apply-dashboard")?.addEventListener("click", () => {
    onApplyDashboard();
  });

  // 최초 진입 시 자동 로딩
  onApplyDashboard();
});

// 연도 선택 셀렉트 채우기
function initYearSelects() {
  const startSel = document.getElementById("year-start");
  const endSel = document.getElementById("year-end");
  if (!startSel || !endSel) return;

  startSel.innerHTML = "";
  endSel.innerHTML = "";

  for (let y = YEAR_MIN; y <= YEAR_MAX; y++) {
    const opt1 = document.createElement("option");
    opt1.value = y;
    opt1.textContent = y;
    startSel.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = y;
    opt2.textContent = y;
    endSel.appendChild(opt2);
  }

  // URL/상태 반영
  startSel.value = String(selectedStartYear);
  endSel.value = String(selectedEndYear);
}

// 지역 체크박스 생성
function initRegionCheckboxes() {
  const box = document.getElementById("control-region-checkboxes");
  if (!box) return;

  box.innerHTML = "";

  SEOUL_GU_LIST.forEach((gu) => {
    const id = `chk-${gu}`;

    const wrap = document.createElement("div");
    wrap.className = "form-check";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.className = "form-check-input";
    input.id = id;
    input.value = gu;

    if (selectedRegions.includes(gu)) input.checked = true;

    input.addEventListener("change", onRegionCheckboxChange);

    const label = document.createElement("label");
    label.className = "form-check-label";
    label.setAttribute("for", id);
    label.textContent = gu;

    wrap.appendChild(input);
    wrap.appendChild(label);
    box.appendChild(wrap);
  });

  // 2개 초과 선택 방지 UI 반영
  enforceMaxTwoSelection();
}

function onRegionCheckboxChange(e) {
  const gu = e.target.value;

  if (e.target.checked) {
    if (selectedRegions.length >= 2) {
      e.target.checked = false;
      alert("지역은 최대 2개까지만 선택할 수 있습니다.");
      return;
    }
    selectedRegions.push(gu);
  } else {
    selectedRegions = selectedRegions.filter((r) => r !== gu);
  }

  // 최소 1개는 유지(대시보드 UX)
  if (selectedRegions.length === 0) {
    selectedRegions = ["강남구"];
    // 체크박스 다시 맞춤
    document.querySelectorAll("#control-region-checkboxes input[type='checkbox']").forEach((chk) => {
      chk.checked = chk.value === "강남구";
    });
  }

  enforceMaxTwoSelection();
}

function enforceMaxTwoSelection() {
  const checkboxes = document.querySelectorAll("#control-region-checkboxes input[type='checkbox']");
  const disableOthers = selectedRegions.length >= 2;

  checkboxes.forEach((chk) => {
    if (!chk.checked) {
      chk.disabled = disableOthers;
    } else {
      chk.disabled = false;
    }
  });
}

// ------------------------------
// 적용 버튼 로직
// ------------------------------
async function onApplyDashboard() {
  const startSel = document.getElementById("year-start");
  const endSel = document.getElementById("year-end");
  if (!startSel || !endSel) return;

  const btn = document.getElementById("btn-apply-dashboard");
  const oldText = btn?.textContent;

  if (btn) {
    btn.disabled = true;
    btn.textContent = "로딩 중...";
  }

  try {
    selectedStartYear = clampYear(parseInt(startSel.value, 10) || YEAR_MIN);
    selectedEndYear = clampYear(parseInt(endSel.value, 10) || YEAR_MAX);

    if (selectedStartYear > selectedEndYear) {
      const tmp = selectedStartYear;
      selectedStartYear = selectedEndYear;
      selectedEndYear = tmp;
      startSel.value = String(selectedStartYear);
      endSel.value = String(selectedEndYear);
    }

    // ✅ URL 상태 저장
    writeDashboardStateToUrl();

    // 구 × 연도 그리드 업데이트
    renderYearRegionGrid();

    // 첫 번째 슬롯
    await loadRegionSlot(1, selectedRegions[0]);

    // 두 번째 슬롯: 선택된 지역이 2개일 때만
    if (selectedRegions.length === 2) {
      await loadRegionSlot(2, selectedRegions[1]);
      document.getElementById("graph-column-2")?.classList.remove("d-none");
    } else {
      document.getElementById("graph-column-2")?.classList.add("d-none");
    }
  } catch (err) {
    console.error("[dashboard] onApplyDashboard error:", err);
    alert(`대시보드를 불러오지 못했습니다.\n${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = oldText || "선택 완료";
    }
  }
}

// ------------------------------
// 슬롯 로딩(지역 1개에 대해 4개 차트 갱신)
// ------------------------------
async function loadRegionSlot(slot, region) {
  const titleEl = document.getElementById(`region-title-${slot}`);
  if (titleEl) titleEl.textContent = region;

  try {
    const [elderlyRes, lonelyRes] = await Promise.all([
      fetchJson(`/api/elderly/forecast/${encodeURIComponent(region)}`),
      fetchJson(`/api/lonely/forecast?region=${encodeURIComponent(region)}`),
    ]);

    // elderly/lonely는 {"status":"success","data":{history,forecast}} 형태
    const elderlyData = elderlyRes.data || elderlyRes;
    const lonelyData = lonelyRes.data || lonelyRes;

    renderRegionCharts(slot, region, elderlyData, lonelyData);
  } catch (err) {
    console.error("슬롯 로딩 실패:", slot, region, err);
    alert(`[${region}] 데이터를 불러오지 못했습니다.\n${err.message}`);
  }
}

// ------------------------------
// 차트 렌더(슬롯별)
// ------------------------------
function renderRegionCharts(slot, region, elderlyData, lonelyData) {
  const colors = SLOT_COLORS[slot];

  // ----- 노인 인구: history / forecast -----
  const eHistory = (elderlyData.history || [])
    .map((row) => ({ year: extractYear(row), v: extractValue(row) }))
    .filter((row) => row.year != null && row.year >= selectedStartYear && row.year <= selectedEndYear)
    .sort((a, b) => a.year - b.year);

  const eForecastAll = (elderlyData.forecast || [])
    .map((row) => ({ year: extractYear(row), v: extractValue(row) }))
    .filter((row) => row.year != null)
    .sort((a, b) => a.year - b.year);

  // 추세 그래프용 forecast: 연도 범위로 필터링
  const eForecastTrend = eForecastAll.filter(
    (row) => row.year >= selectedStartYear && row.year <= selectedEndYear
  );

  // 추세(선택 구간) = (history + forecastTrend) 정렬
  const eTrendMerged = [...eHistory, ...eForecastTrend].sort((a, b) => a.year - b.year);
  const eTrendYears = eTrendMerged.map((r) => r.year);
  const eTrendValues = eTrendMerged.map((r) => r.v);

  createLineChart(
    `trend-elderly-${slot}`,
    eTrendYears,
    eTrendValues,
    colors.elderlyTrend,
    `${region} 노인 인구 추세`,
    false,
    false
  );

  // 5년 예측(전체 forecast 기준 상위 5개)
  const eForecast5 = eForecastAll.slice(0, 5);
  const eForecastYears = eForecast5.map((r) => r.year);
  const eForecastValues = eForecast5.map((r) => r.v);

  createLineChart(
    `forecast-elderly-${slot}`,
    eForecastYears,
    eForecastValues,
    colors.elderlyForecast,
    `${region} 노인 인구 5년 예측`,
    false,
    true
  );

  // ----- 고독사: history / forecast -----
  const lHistory = (lonelyData.history || [])
    .map((row) => ({ year: extractYear(row), v: extractValue(row) }))
    .filter((row) => row.year != null && row.year >= selectedStartYear && row.year <= selectedEndYear)
    .sort((a, b) => a.year - b.year);

  const lForecastAll = (lonelyData.forecast || [])
    .map((row) => ({ year: extractYear(row), v: extractValue(row) }))
    .filter((row) => row.year != null)
    .sort((a, b) => a.year - b.year);

  const lForecastTrend = lForecastAll.filter(
    (row) => row.year >= selectedStartYear && row.year <= selectedEndYear
  );

  const lTrendMerged = [...lHistory, ...lForecastTrend].sort((a, b) => a.year - b.year);
  const lTrendYears = lTrendMerged.map((r) => r.year);
  const lTrendValues = lTrendMerged.map((r) => r.v);

  createLineChart(
    `trend-lonely-${slot}`,
    lTrendYears,
    lTrendValues,
    colors.lonelyTrend,
    `${region} 고독사 추세`,
    false,
    false
  );

  const lForecast5 = lForecastAll.slice(0, 5);
  const lForecastYears = lForecast5.map((r) => r.year);
  const lForecastValues = lForecast5.map((r) => r.v);

  createLineChart(
    `forecast-lonely-${slot}`,
    lForecastYears,
    lForecastValues,
    colors.lonelyForecast,
    `${region} 고독사 5년 예측`,
    false,
    true
  );
}
```

# FILE: belong/static/css/style.css
```/* static/css/style.css */
/* =========================================
   Belong Global Styles (ONLY GLOBAL)
   - tokens / reset / layout / shared components
   - page-only CSS는 여기 넣지 않는다
========================================= */

/* 0) Design Tokens (전역 변수: 한 곳에서만 관리) */
:root{
  /* Surface */
  --color-bg-main: #f5f7fb;
  --color-bg-card: #ffffff;
  --color-bg-soft-1: #f9fafb;
  --color-bg-soft-2: #f1f5f9;

  /* Text */
  --color-text-main: #0f172a;
  --color-text-sub: rgba(15, 23, 42, 0.68);

  /* Border & Shadow */
  --color-border: rgba(15, 23, 42, 0.12);
  --color-shadow: rgba(15, 23, 42, 0.08);

  /* Brand */
  --color-primary: #2563eb;
  --color-primary-dark: #1d4ed8;
  --color-accent: #3b82f6;

  /* Radius */
  --radius-sm: 10px;
  --radius-md: 14px;
  --radius-lg: 18px;
  --radius-xl: 22px;

  /* Layout */
  --container-max: 1200px;
  --container-pad: 16px;
}

/* 1) Reset / Base */
*,
*::before,
*::after{
  box-sizing: border-box;
}

html, body{
  height: 100%;
}

body{
  margin: 0;
  font-family: "Pretendard", system-ui, -apple-system, Segoe UI, Roboto, "Noto Sans KR", Arial, sans-serif;
  background: var(--color-bg-main);
  color: var(--color-text-main);
  line-height: 1.6;
}

img{
  max-width: 100%;
  height: auto;
  display: block;
}

a{
  color: inherit;
  text-decoration: none;
}

a:hover{
  text-decoration: none;
}

/* 2) Base Layout (base.html에서 쓰는 뼈대) */
.page-grid{
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.site-header{
  width: 100%;
}

.site-main{
  flex: 1 0 auto;
  width: 100%;
}

.site-footer{
  margin-top: auto;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-soft-1);
}

/* 3) Global Container / Section helper */
.page-container{
  width: min(var(--container-max), 100%);
  margin: 0 auto;
  padding: 0 var(--container-pad);
}

.section{
  padding: 24px 0;
}

/* 4) Shared Components (전역 공통 컴포넌트만) */
.card-soft{
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 28px var(--color-shadow);
  overflow: hidden;
}

/* Bootstrap 버튼: 전역은 최소만 (안전하게) */
.btn{
  border-radius: var(--radius-md);
}

.btn.btn-primary{
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  border: 0;
}

.btn.btn-primary:hover{
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-accent));
  border: 0;
}

.btn.btn-outline-primary{
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.btn.btn-outline-primary:hover{
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

/* 5) Utilities (필요 최소만) */
.u-soft-bg{
  background: var(--color-bg-soft-2);
}

.u-border{
  border: 1px solid var(--color-border);
}

.u-rounded-lg{
  border-radius: var(--radius-lg);
}

.u-shadow-soft{
  box-shadow: 0 10px 28px var(--color-shadow);
}
/* Coming soon links (clickable but visually muted) */
.is-coming-soon{
  opacity: .75;
}

.is-coming-soon:hover{
  opacity: 1;
  cursor: pointer;
}
```

# FILE: belong/static/css/home.css
```/* static/css/home.css */
/* PAGE ONLY: Home (index) */

.home-page .hero-section{
  padding: 28px 0 18px;
}

.home-page .hero-grid{
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

@media (min-width: 992px){
  .home-page .hero-grid{
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
    gap: 22px;
    align-items: stretch;
  }
}

.home-page .hero-eyebrow{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: .06em;
  font-weight: 700;
  color: rgba(29, 78, 216, 0.95);
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.22);
}

.home-page .hero-title{
  margin: 14px 0 10px;
  font-weight: 800;
  line-height: 1.15;
  font-size: clamp(28px, 3.4vw, 44px);
  color: var(--color-text-main);
}

.home-page .hero-subtitle{
  margin: 0 0 14px;
  color: var(--color-text-sub);
  font-size: 15px;
  line-height: 1.75;
}

.home-page .hero-meta{
  margin-top: 10px;
  font-size: 13px;
  color: rgba(15, 23, 42, 0.62);
}

.home-page .hero-meta a{
  color: rgba(29, 78, 216, 0.95);
}

.home-page .hero-visual{
  min-height: 100%;
}

.home-page .hero-visual-card{
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid var(--color-border);
  box-shadow: 0 14px 34px var(--color-shadow);
}

.home-page .hero-visual-media{
  aspect-ratio: 16 / 9;
  background: #111827;
}

.home-page .hero-image{
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.95;
}

.home-page .hero-visual-text{
  padding: 16px 18px 18px;
  background: var(--color-bg-card);
}

.home-page .hero-visual-title{
  font-weight: 800;
  color: var(--color-text-main);
  margin-bottom: 6px;
}

.home-page .hero-visual-desc{
  color: var(--color-text-sub);
  font-size: 13px;
  line-height: 1.65;
}

/* Features section */
.home-page .services-section{
  padding: 18px 0 26px;
}

.home-page .feature-card-title{
  font-weight: 800;
  margin-bottom: 8px;
}

.home-page .feature-card-desc{
  color: var(--color-text-sub);
  line-height: 1.7;
  margin-bottom: 14px;
}

/* How-to section (배경/여백만 전용 처리) */
.home-page .how-section{
  padding: 44px 0;
  background: #f8fafc;
}

.home-page .how-card-title{
  font-weight: 800;
  margin-bottom: 8px;
}

.home-page .how-card-desc{
  color: var(--color-text-sub);
  line-height: 1.7;
}

/* Roadmap section */
.home-page .roadmap-section{
  padding: 44px 0 52px;
}

.home-page .roadmap-title{
  font-weight: 800;
  margin-bottom: 8px;
}

.home-page .roadmap-desc{
  color: var(--color-text-sub);
  line-height: 1.7;
}
```

# FILE: belong/static/css/dashboard.css
```/* static/css/dashboard.css */
/* =========================================
   Belong Dashboard Styles (PAGE ONLY)
   Scope: .dashboard-section ONLY
   - 전역(style.css / bootstrap)과 충돌 최소화
   - "아래에 덧붙이는 패치" 없이 한 파일로 완결
========================================= */

.dashboard-section{
  /* ✅ 페이지 전용 토큰 (전역 :root 금지) */
  --bd-surface: #ffffff;
  --bd-surface-2: #f7f9fc;
  --bd-border: rgba(15, 23, 42, 0.12);
  --bd-text: #0f172a;
  --bd-muted: rgba(15, 23, 42, 0.65);
  --bd-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  --bd-radius: 18px;

  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 60%);
  min-height: calc(100vh - 160px);
}

/* =========================
   카드(soft) - 대시보드에서만 보정
========================= */
.dashboard-section .card-soft{
  border: 1px solid var(--bd-border);
  border-radius: var(--bd-radius);
  background: var(--bd-surface);
  box-shadow: var(--bd-shadow);
}

/* =========================
   레이아웃 안정화
   - 좁은 화면에서 요소가 튀는 문제 방지
========================= */

/* 좌측 컨트롤 카드 내부 overflow로 튐 방지 */
.dashboard-section .dashboard-sidebar .card-body{
  overflow: hidden;
}

/* 데스크탑에서 사이드바 sticky (UX 향상 + 레이아웃 안정) */
@media (min-width: 992px){
  .dashboard-section .dashboard-sidebar{
    position: sticky;
    top: 84px; /* 네비 높이에 맞춰 필요 시 조정 */
    align-self: start;
  }
}

/* 모바일에서 사이드바 padding 축소 */
@media (max-width: 991.98px){
  .dashboard-section .dashboard-sidebar .card-body{
    padding: 16px;
  }
}

/* =========================
   좌측 컨트롤(체크박스 리스트)
========================= */
.dashboard-section .region-checkbox-list{
  border: 1px solid var(--bd-border);
  border-radius: 14px;
  background: var(--bd-surface-2);
  padding: 10px;
  max-height: 260px;
  overflow: auto;
}

.dashboard-section .region-checkbox-list .form-check{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px;
  border-radius: 10px;
}

.dashboard-section .region-checkbox-list .form-check:hover{
  background: rgba(37, 99, 235, 0.06);
}

.dashboard-section .region-checkbox-list .form-check-label{
  font-size: 0.93rem;
  color: var(--bd-text);
}

.dashboard-section #btn-apply-dashboard{
  border-radius: 14px;
  font-weight: 700;
}

/* =========================
   구×연도 그리드 (튐/깨짐 해결 핵심)
========================= */
.dashboard-section #year-region-grid{
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

.dashboard-section .year-region-grid-wrap{
  border: 1px solid var(--bd-border);
  border-radius: 14px;
  overflow: hidden; /* 기본은 숨김 */
  background: #fff;
}

/* 좁은 화면에서는 표 가로 스크롤 허용 */
@media (max-width: 575.98px){
  .dashboard-section .year-region-grid-wrap{
    overflow-x: auto;
  }
}

.dashboard-section .year-region-grid-wrap table{
  margin: 0;
  width: 100%;
}

/* 너무 좁아지면 열이 깨지므로 최소폭 + fixed */
@media (max-width: 575.98px){
  .dashboard-section .year-region-grid-wrap table{
    min-width: 520px;
  }
}

.dashboard-section .year-region-grid-wrap thead th{
  background: #f1f6ff;
  color: var(--bd-text);
  font-weight: 700;
  font-size: 0.85rem;
  white-space: nowrap;
}

.dashboard-section .year-region-grid-wrap tbody td{
  font-size: 0.85rem;
  color: var(--bd-text);
  vertical-align: middle;
}

.dashboard-section .year-region-grid-cell{
  text-align: center;
  color: rgba(15, 23, 42, 0.45);
  user-select: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-section .year-region-grid-cell:hover{
  background: rgba(37, 99, 235, 0.06);
  color: rgba(37, 99, 235, 0.95);
}

/* =========================
   우측 차트 영역 (높이 균일화 + 타이틀 정렬 준비)
========================= */

/* 슬롯(지역 카드) 내부 제목줄 정렬 */
.dashboard-section .slot-header{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.dashboard-section .slot-title{
  font-weight: 800;
  margin: 0;
}

/* 차트 타이틀(소제목) 높이 균일화: 2줄까지 고정 */
.dashboard-section .chart-title{
  min-height: 34px;      /* 두 줄 정도 공간 확보 */
  display: flex;
  align-items: flex-end;
  font-size: 0.9rem;
  font-weight: 700;
  margin-bottom: 6px;
}

/* 차트 박스: 모든 차트 동일 높이 */
.dashboard-section .chart-wrapper{
  position: relative;
  height: 240px;         /* ✅ 기본 높이 통일 */
  border: 1px solid var(--bd-border);
  background: #fff;
  border-radius: 14px;
  padding: 10px;
}

.dashboard-section .chart-wrapper canvas{
  width: 100% !important;
  height: 100% !important;
}

/* 버튼 라운드(대시보드 내부 한정) */
.dashboard-section .btn{
  border-radius: 12px;
}

/* =========================
   반응형: 2열 → 1열 전환 시 여백/정렬
========================= */

/* 태블릿 이하: 차트 높이 살짝 증가 */
@media (max-width: 991.98px){
  .dashboard-section .region-checkbox-list{
    max-height: 200px;
  }

  .dashboard-section .chart-wrapper{
    height: 260px;
  }
}

/* 모바일: 차트 높이 추가 + 타이틀 간격 정리 */
@media (max-width: 575.98px){
  .dashboard-section .chart-wrapper{
    height: 280px;
  }

  .dashboard-section .chart-title{
    min-height: 38px;
  }
}
```

# FILE: belong/static/css/ai.css
```/* static/css/ai.css */
/* PAGE ONLY: AI Hub (ai_tool.html) */

.ai-page .ai-hero{
  margin-bottom: 18px;
}

/* 기능 카드(빠른 선택) */
.ai-page .ai-feature-grid{
  margin-bottom: 18px;
}

.ai-page .ai-feature-card{
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  box-shadow: 0 10px 28px var(--color-shadow);
  overflow: hidden;
}

.ai-page .ai-feature-card .card-body{
  padding: 18px;
}

.ai-page .ai-feature-title{
  font-weight: 800;
  margin: 0;
}

.ai-page .ai-feature-desc{
  margin: 10px 0 14px;
  color: var(--color-text-sub);
  line-height: 1.7;
  font-size: 14px;
}

/* 실행 콘솔 */
.ai-page .ai-console{
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  box-shadow: 0 14px 34px var(--color-shadow);
}

.ai-page .ai-console .card-body{
  padding: 18px;
}

@media (min-width: 992px){
  .ai-page .ai-console .card-body{
    padding: 28px;
  }
}

.ai-page .ai-console-header{
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}

@media (min-width: 992px){
  .ai-page .ai-console-header{
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
  }
}

.ai-page .ai-console-title{
  font-weight: 800;
  margin: 0;
}

.ai-page .ai-console-subtitle{
  color: var(--color-text-sub);
  font-size: 13px;
}

.ai-page .ai-form-help{
  font-size: 13px;
  color: rgba(15, 23, 42, 0.58);
}

/* 결과창(채팅 박스) */
.ai-page .ai-chat-box{
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 14px;
  min-height: 160px;
  max-height: 420px;
  overflow-y: auto;
  background: #fff;
}

/* 카드 클릭 버튼의 일관성 */
.ai-page .ai-quick-select{
  border-radius: var(--radius-md);
}
```