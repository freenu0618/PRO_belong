// static/charts/dashboard.js
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
