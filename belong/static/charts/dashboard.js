// =======================================
// Belong 대시보드 v2
// - 좌측: 연도 / 지역 선택 (최대 2개)
// - 우측: 각 지역별 4개 그래프
//   1) 독거노인 추세
//   2) 고독사 추세
//   3) 독거노인 5년 예측
//   4) 고독사 5년 예측
// =======================================

// ----- 설정 -----
const YEAR_MIN = 2017;
const YEAR_MAX = 2035;

// 서울 전체(옵션) + 25개 구
const ALL_REGIONS = [
  "서울 전체",
  "강남구", "강동구", "강북구", "강서구",
  "관악구", "광진구", "구로구", "금천구",
  "노원구", "도봉구", "동대문구", "동작구",
  "마포구", "서대문구", "서초구", "성동구",
  "성북구", "송파구", "양천구", "영등포구",
  "용산구", "은평구", "종로구", "중구", "중랑구",
];

// 기본 선택 지역
let selectedRegions = ["강남구", "종로구"];

// 연도 선택 상태
let selectedStartYear = 2017;
let selectedEndYear = 2023;

// Chart 인스턴스 보관
const chartStore = {};

// 슬롯별 색상 팔레트
const SLOT_COLORS = {
  1: {
    elderlyTrend: "#6366F1",
    lonelyTrend: "#EC4899",
    elderlyForecast: "#A855F7",
    lonelyForecast: "#F97316",
  },
  2: {
    elderlyTrend: "#0EA5E9",
    lonelyTrend: "#EF4444",
    elderlyForecast: "#22C55E",
    lonelyForecast: "#22C55E",
  },
};

// ------------------------------
// 공통 유틸
// ------------------------------
async function fetchJson(url) {
  const res = await fetch(url);
  let json;
  try {
    json = await res.json();
  } catch (e) {
    console.error("JSON 파싱 실패:", url, e);
    throw new Error("서버 응답을 해석할 수 없습니다.");
  }
  if (!res.ok || (json.status && json.status.toLowerCase() === "error")) {
    const msg = json.message || `요청 실패 (${res.status})`;
    throw new Error(msg);
  }
  return json;
}

function createLineChart(canvasId, labels, data, color, label, dashed = false, fill = false) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

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
          backgroundColor: fill ? color + "33" : color,
          borderWidth: 2,
          fill: fill,
          tension: 0.35,
          pointRadius: 3,
          pointHoverRadius: 4,
          spanGaps: true,
          borderDash: dashed ? [6, 4] : [],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          mode: "index",
          intersect: false,
          callbacks: {
            label: (ctx) => ctx.parsed.y?.toLocaleString("ko-KR") || "0",
          },
        },
      },
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
// 초기화
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initYearSelects();
  initRegionCheckboxes();

  document
    .getElementById("btn-apply-dashboard")
    ?.addEventListener("click", onApplyDashboard);

  // 페이지 최초 진입 시 강남구 / 종로구 바로 로딩
  onApplyDashboard();
});

// 연도 선택 셀렉트 채우기
function initYearSelects() {
  const startSel = document.getElementById("year-start");
  const endSel = document.getElementById("year-end");
  if (!startSel || !endSel) return;

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

  startSel.value = String(selectedStartYear);
  endSel.value = String(selectedEndYear);

  startSel.addEventListener("change", () => {
    selectedStartYear = parseInt(startSel.value, 10) || YEAR_MIN;
  });
  endSel.addEventListener("change", () => {
    selectedEndYear = parseInt(endSel.value, 10) || YEAR_MAX;
  });
}

// 지역 체크박스 생성
function initRegionCheckboxes() {
  const container = document.getElementById("control-region-checkboxes");
  if (!container) return;

  container.innerHTML = "";

  ALL_REGIONS.forEach((name) => {
    const id = `chk-region-${name}`;

    const wrap = document.createElement("div");
    wrap.className = "form-check";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.className = "form-check-input";
    input.id = id;
    input.name = "region";
    input.value = name;

    if (selectedRegions.includes(name)) {
      input.checked = true;
    }

    input.addEventListener("change", onRegionCheckboxChange);

    const label = document.createElement("label");
    label.className = "form-check-label";
    label.setAttribute("for", id);
    label.textContent = name;

    wrap.appendChild(input);
    wrap.appendChild(label);
    container.appendChild(wrap);
  });
}

// 최대 2개까지 체크
function onRegionCheckboxChange(e) {
  const checked = Array.from(
    document.querySelectorAll('#control-region-checkboxes input[name="region"]:checked')
  );

  if (checked.length > 2) {
    e.target.checked = false;
    alert("지역은 최대 2개까지 선택할 수 있습니다.");
    return;
  }
}

// "선택 완료" 클릭 시
async function onApplyDashboard() {
  const startSel = document.getElementById("year-start");
  const endSel = document.getElementById("year-end");
  if (!startSel || !endSel) return;

  selectedStartYear = parseInt(startSel.value, 10) || YEAR_MIN;
  selectedEndYear = parseInt(endSel.value, 10) || YEAR_MAX;

  if (selectedStartYear > selectedEndYear) {
    const tmp = selectedStartYear;
    selectedStartYear = selectedEndYear;
    selectedEndYear = tmp;
    startSel.value = String(selectedStartYear);
    endSel.value = String(selectedEndYear);
  }

  const checked = Array.from(
    document.querySelectorAll('#control-region-checkboxes input[name="region"]:checked')
  ).map((el) => el.value);

  if (checked.length === 0) {
    alert("최소 1개 이상의 지역을 선택해주세요.");
    return;
  }
  if (checked.length > 2) {
    alert("지역은 최대 2개까지 선택할 수 있습니다.");
    return;
  }

  selectedRegions = checked;

  // 첫 번째 슬롯
  await loadRegionSlot(1, selectedRegions[0]);

  // 두 번째 슬롯: 선택된 지역이 2개일 때만
  if (selectedRegions.length === 2) {
    await loadRegionSlot(2, selectedRegions[1]);
    document.getElementById("graph-column-2")?.classList.remove("d-none");
  } else {
    // 한 개만 선택한 경우 오른쪽 컬럼 숨김
    document.getElementById("graph-column-2")?.classList.add("d-none");
  }
}

// 한 슬롯(1 or 2)에 대해 데이터 로딩 + 그래프 렌더
async function loadRegionSlot(slot, region) {
  const titleEl = document.getElementById(`region-title-${slot}`);
  if (titleEl) {
    titleEl.textContent = region;
  }

  try {
    const [elderlyRes, lonelyRes] = await Promise.all([
      fetchJson(`/api/elderly/forecast/${encodeURIComponent(region)}`),
      fetchJson(`/api/lonely/forecast?region=${encodeURIComponent(region)}`),
    ]);

    const elderlyData = elderlyRes.data || elderlyRes;
    const lonelyData = lonelyRes.data || lonelyRes;

    renderRegionCharts(slot, region, elderlyData, lonelyData);
  } catch (err) {
    console.error("슬롯 로딩 실패:", slot, region, err);
    alert(`[${region}] 데이터를 불러오지 못했습니다.\n${err.message}`);
  }
}

// 실제 그래프 4개 렌더링
function renderRegionCharts(slot, region, elderlyData, lonelyData) {
  const colors = SLOT_COLORS[slot];

  // ----- 노인 인구: history / forecast -----
  const eHistory = (elderlyData.history || []).filter(
    (row) => row.year >= selectedStartYear && row.year <= selectedEndYear
  );
  const eForecastAll = (elderlyData.forecast || []).sort((a, b) => a.year - b.year);

  // 추세 그래프용 (history + forecast 전체)
  const eTrendYears = [...eHistory, ...eForecastAll].map((r) => r.year);
  const eTrendValues = [...eHistory, ...eForecastAll].map((r) => r.value || 0);

  createLineChart(
    `trend-elderly-${slot}`,
    eTrendYears,
    eTrendValues,
    colors.elderlyTrend,
    `${region} 독거노인 추세`,
    false,
    false
  );

  // 5년 예측용
  const eForecast5 = eForecastAll.slice(0, 5);
  const eForecastYears = eForecast5.map((r) => r.year);
  const eForecastValues = eForecast5.map((r) => r.value || 0);

  createLineChart(
    `forecast-elderly-${slot}`,
    eForecastYears,
    eForecastValues,
    colors.elderlyForecast,
    `${region} 독거노인 5년 예측`,
    false,
    true
  );

  // ----- 고독사: history / forecast -----
  const lHistory = (lonelyData.history || []).filter(
    (row) => row.year >= selectedStartYear && row.year <= selectedEndYear
  );
  const lForecastAll = (lonelyData.forecast || []).sort((a, b) => a.year - b.year);

  const lTrendYears = [...lHistory, ...lForecastAll].map((r) => r.year);
  const lTrendValues = [...lHistory, ...lForecastAll].map((r) => r.value || 0);

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
  const lForecastValues = lForecast5.map((r) => r.value || 0);

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
