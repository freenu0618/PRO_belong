// static/js/region_predict.js
// =====================================
// 지역 예측(단일 지역 + 단일 연도) 페이지용
// - 실측(2017~2023) + 선택 연도 예측(POST /api/predictions/<region>/<year>)
// - 예측 이력(GET /api/predictions/history/<region>)
// - Chart.js 2개: (1) 실측+선택예측 (2) 예측이력
//
// 이 스크립트가 기대하는 DOM id:
//  - loading, error-message
//  - summary-section, latest-pop, predicted-pop, growth-rate
//  - forecast-chart (canvas), prediction-history-chart (canvas)
//  - chart-btn-section, history-section, predict-form, predict-year
// =====================================

let currentRegion = null;
let currentYear = null;

let mainChartInstance = null;       // 실측 + 선택 예측 차트
let historyChartInstance = null;    // 예측 이력 차트

const ACTUAL_START_YEAR = 2017;
const ACTUAL_END_YEAR = 2023; // 실측 마지막 연도(현재 백엔드 기준)
const YEAR_MIN = 2017;
const YEAR_MAX = 2035;

// ---------------------
// 공통 유틸
// ---------------------
function clampYear(y) {
  if (!Number.isFinite(y)) return ACTUAL_END_YEAR;
  return Math.min(YEAR_MAX, Math.max(YEAR_MIN, y));
}

function ensureChartJs() {
  if (typeof Chart === "undefined") {
    throw new Error("Chart.js가 로드되지 않았습니다. (Chart is undefined)");
  }
}

function showLoading() {
  const el = document.getElementById("loading");
  if (el) el.style.display = "block";
}

function hideLoading() {
  const el = document.getElementById("loading");
  if (el) el.style.display = "none";
}

function showError(msg) {
  const el = document.getElementById("error-message");
  if (!el) return;
  el.innerText = msg;
  el.style.display = "block";
}

function hideError() {
  const el = document.getElementById("error-message");
  if (!el) return;
  el.innerText = "";
  el.style.display = "none";
}

function showSection(id, show) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.display = show ? "block" : "none";
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText}`);
  }
  return await res.json();
}

// ---------------------
// 1) 실측 히스토리(노인) 조회
// GET /api/elderly-stats/<region>/<start>/<end>
// 응답: [ {year, elderly_population}, ... ]
// ---------------------
async function fetchHistory(region) {
  const url = `/api/elderly-stats/${encodeURIComponent(region)}/${ACTUAL_START_YEAR}/${ACTUAL_END_YEAR}`;
  const json = await fetchJson(url);

  if (!Array.isArray(json) || json.length === 0) {
    throw new Error("히스토리 데이터 형식 오류 또는 비어 있음");
  }

  // 정렬 보장
  return json
    .map((r) => ({
      year: Number(r.year),
      elderly_population: Number(r.elderly_population),
    }))
    .filter((r) => Number.isFinite(r.year) && Number.isFinite(r.elderly_population))
    .sort((a, b) => a.year - b.year);
}

// ---------------------
// 2) 선택 연도 예측 요청(저장 포함)
// POST /api/predictions/<region>/<year>
// 응답: { saved: true, result: { year, prediction, ... } }
// ---------------------
async function fetchPrediction(region, year) {
  const y = clampYear(Number(year));
  const url = `/api/predictions/${encodeURIComponent(region)}/${y}`;

  const json = await fetchJson(url, { method: "POST" });

  // 서버가 {result:{...}} 형태로 주는 것을 기대
  if (!json || typeof json !== "object" || !json.result) {
    throw new Error("예측 데이터 형식 오류");
  }

  const result = json.result;
  const predYear = Number(result.year);
  const predVal = Number(result.prediction);

  if (!Number.isFinite(predYear) || !Number.isFinite(predVal)) {
    throw new Error("예측 결과 값이 유효하지 않습니다.");
  }

  return { year: predYear, prediction: predVal };
}

// ---------------------
// 3) 예측 이력 조회
// GET /api/predictions/history/<region>
// 응답: [ {region, year, prediction, ...}, ... ]
// ---------------------
async function fetchPredictionHistory(region) {
  const url = `/api/predictions/history/${encodeURIComponent(region)}`;
  const json = await fetchJson(url);

  if (!Array.isArray(json)) return [];

  return json
    .map((r) => ({
      year: Number(r.year),
      prediction: Number(r.prediction),
      created_at: r.created_at || null,
      source: r.source || null,
    }))
    .filter((r) => Number.isFinite(r.year) && Number.isFinite(r.prediction))
    .sort((a, b) => a.year - b.year);
}

// ---------------------
// 4) 요약 정보 표시
// ---------------------
function renderSummary(history, predictionObj) {
  const latestRow = history[history.length - 1];
  const latest = Number(latestRow.elderly_population);
  const predicted = Number(predictionObj.prediction);

  if (!Number.isFinite(latest) || !Number.isFinite(predicted)) {
    showSection("summary-section", false);
    return;
  }

  const growth =
    latest > 0 ? (((predicted - latest) / latest) * 100).toFixed(1) : "0.0";

  const latestEl = document.getElementById("latest-pop");
  const predEl = document.getElementById("predicted-pop");
  const growthEl = document.getElementById("growth-rate");

  if (latestEl) latestEl.innerText = latest.toLocaleString();
  if (predEl) predEl.innerText = predicted.toLocaleString();
  if (growthEl) growthEl.innerText = `${growth}%`;

  showSection("summary-section", true);
}

// ---------------------
// 5) 메인 차트(실측 + 선택 예측)
// ---------------------
function renderMainChart(history, predictionObj) {
  ensureChartJs();

  const canvas = document.getElementById("forecast-chart");
  if (!canvas) return;

  const labels = history.map((r) => r.year);
  const values = history.map((r) => r.elderly_population);

  // 예측점 추가
  const predYear = predictionObj.year;
  const predVal = predictionObj.prediction;

  // 예측 연도가 실측 범위 안이면, 해당 연도에 찍어서 비교(선택 예측 강조)
  // 예측 연도가 실측 밖이면, 뒤에 추가
  let mergedLabels = [...labels];
  let mergedValues = [...values];
  let predIndex = -1;

  const idx = mergedLabels.indexOf(predYear);
  if (idx >= 0) {
    predIndex = idx;
    mergedValues[idx] = predVal;
  } else {
    mergedLabels.push(predYear);
    mergedValues.push(predVal);
    // 연도 정렬 유지
    const zipped = mergedLabels.map((y, i) => ({ y, v: mergedValues[i] }));
    zipped.sort((a, b) => a.y - b.y);
    mergedLabels = zipped.map((z) => z.y);
    mergedValues = zipped.map((z) => z.v);
    predIndex = mergedLabels.indexOf(predYear);
  }

  // 포인트 스타일(예측점만 강조)
  const pointRadius = mergedLabels.map((_, i) => (i === predIndex ? 6 : 3));
  const pointBg = mergedLabels.map((_, i) => (i === predIndex ? "#dc3545" : "#0d6efd"));

  if (mainChartInstance) mainChartInstance.destroy();

  mainChartInstance = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: mergedLabels,
      datasets: [
        {
          label: "노인 인구(실측/선택예측)",
          data: mergedValues,
          borderColor: "#0d6efd",
          backgroundColor: "rgba(13,110,253,0.10)",
          tension: 0.35,
          pointRadius,
          pointBackgroundColor: pointBg,
          spanGaps: true,
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
        x: { title: { display: true, text: "연도" } },
        y: { title: { display: true, text: "인구(명)" }, beginAtZero: false },
      },
    },
  });
}

// ---------------------
// 6) 예측 이력 차트
// ---------------------
function renderHistoryChart(historyList) {
  ensureChartJs();

  const section = document.getElementById("history-section");
  const canvas = document.getElementById("prediction-history-chart");

  if (!section || !canvas) return;

  if (!Array.isArray(historyList) || historyList.length === 0) {
    section.style.display = "none";
    return;
  }

  section.style.display = "block";

  const sorted = [...historyList].sort((a, b) => a.year - b.year);
  const labels = sorted.map((r) => r.year);
  const data = sorted.map((r) => r.prediction);

  if (historyChartInstance) historyChartInstance.destroy();

  historyChartInstance = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "예측 이력",
          data,
          borderColor: "#198754",
          backgroundColor: "rgba(25,135,84,0.12)",
          tension: 0.35,
          pointRadius: 3,
          spanGaps: true,
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
        x: { title: { display: true, text: "연도" } },
        y: { title: { display: true, text: "예측값" }, beginAtZero: false },
      },
    },
  });
}

// ---------------------
// 7) 전체 로딩 플로우
// ---------------------
async function loadRegionForecast(region, year) {
  hideError();
  showLoading();

  try {
    currentRegion = (region || "").trim();
    currentYear = clampYear(Number(year));

    if (!currentRegion) {
      throw new Error("region이 비어있습니다.");
    }

    // 실측 + 예측 + 예측이력
    const [history, prediction, predHistory] = await Promise.all([
      fetchHistory(currentRegion),
      fetchPrediction(currentRegion, currentYear),
      fetchPredictionHistory(currentRegion).catch(() => []), // 이력 실패해도 메인은 살림
    ]);

    // 요약
    renderSummary(history, prediction);

    // 차트
    renderMainChart(history, prediction);
    renderHistoryChart(predHistory);

    // 버튼/섹션 노출
    showSection("chart-btn-section", true);

    hideLoading();

    // 자동 스크롤(원하면 제거 가능)
    setTimeout(() => {
      window.scrollTo({ top: 400, behavior: "smooth" });
    }, 300);
  } catch (err) {
    console.error(err);
    hideLoading();
    showSection("summary-section", false);
    showSection("chart-btn-section", false);
    showSection("history-section", false);
    showError("데이터를 불러오지 못했습니다. 입력값을 확인해주세요.");
  }
}

// ---------------------
// 8) 페이지 초기화
// - 템플릿에서 initRegionDetail(region, year) 형태로 호출하던 것을 유지
// - 새 이름 initRegionPredictPage도 같이 제공(호환)
// ---------------------
function initRegionDetail(region, year) {
  const r = (region || "").trim();
  const y = clampYear(Number(year));

  // 폼 이벤트: 연도만 바꿔 재조회
  const form = document.getElementById("predict-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const yearInput = document.getElementById("predict-year");
      if (!yearInput) return;

      const newYear = clampYear(Number(yearInput.value));
      yearInput.value = String(newYear);

      await loadRegionForecast(r, newYear);
    });
  }

  // 첫 로딩
  loadRegionForecast(r, y);
}

// alias
function initRegionPredictPage(region, year) {
  initRegionDetail(region, year);
}

window.initRegionDetail = initRegionDetail;
window.initRegionPredictPage = initRegionPredictPage;
