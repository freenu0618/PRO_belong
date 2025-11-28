// =======================================
// Belong 대시보드 스크립트
// - 노인 인구 / 고독사 추세
// - TOP5 테이블 4종
// - 구별 예측 모달
// - 메인 차트에서 구별 라인 on/off
// =======================================

// ------------------------------
// 전역 상태
// ------------------------------
let dashboardChart = null;        // 메인 노인 인구 추세
let lonelyChart = null;           // 메인 고독사 추세
let forecastChart = null;         // [노인 인구] 모달 차트
let lonelyForecastChart = null;   // [고독사] 모달 차트

let elderlyMainTrend = null;      // /api/elderly/trend 결과 캐시

// 메인 차트에서 선택된 구
const selectedRegions = new Set();
// 구별 예측 시리즈 캐시: { "강남구": [ {year, value}, ... ] }
const regionSeriesCache = {};

// 서울 25개 구 리스트 (정렬된 상태라고 가정)
const SEOUL_REGIONS = [
  "강남구", "강동구", "강북구", "강서구",
  "관악구", "광진구", "구로구", "금천구",
  "노원구", "도봉구", "동대문구", "동작구",
  "마포구", "서대문구", "서초구", "성동구",
  "성북구", "송파구", "양천구", "영등포구",
  "용산구", "은평구", "종로구", "중구", "중랑구"
];

// 전체(서울 합계) 라인 표시 여부
let showTotal = true;
// 🔹 고독사 전체 추세 + 구별 예측 캐시
let lonelyMainTrend = [];                    // /api/lonely/trend 데이터 (서울 전체)
const selectedLonelyRegions = new Set();     // 체크된 구 (고독사)
const lonelyRegionSeriesCache = {};          // { region: [{year, value}, ...] }
let showLonelyTotal = true;                  // 서울 전체 라인 표시 여부

// ------------------------------
// 유틸 함수들
// ------------------------------

// 문자열 기반 HSL 색상 생성 (구별 라인용)
function getColorForRegion(region) {
  let hash = 0;
  for (let i = 0; i < region.length; i++) {
    hash = region.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 65%, 50%)`;
}

// fetch + 에러 처리 공통 래퍼
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

// Chart.js dataset 생성
function createLineDataset(label, data, color, dashed = false) {
  return {
    label,
    data,                  // [ {x: year, y: value}, ... ]
    borderColor: color,
    backgroundColor: color,
    borderWidth: 2,
    fill: false,
    tension: 0.1,
    spanGaps: true,
    pointRadius: 2,
    borderDash: dashed ? [6, 4] : [],
    yAxisID: "y"
  };
}

// ------------------------------
// 1) 초기화
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initDashboard().catch((err) => {
    console.error("대시보드 초기화 오류:", err);
    alert("대시보드를 불러오는 중 오류가 발생했습니다.");
  });
});

async function initDashboard() {
  // 구 체크박스
  initRegionCheckboxes();

  // 버튼/입력 이벤트 바인딩
  bindForecastButtons();

  // 주요 데이터 병렬로 로딩
  await Promise.all([
    loadElderlyTrend(),
    loadLonelyTrend(),
    loadTop5Tables()
  ]);
}

// ------------------------------
// 2) 노인 인구 추세 (메인 차트)
// ------------------------------
async function loadElderlyTrend() {
  try {
    const json = await fetchJson(
      "/api/elderly/trend?start_year=2017&end_year=2035"
    );
    const items = json.items || json.data || [];

    elderlyMainTrend = items;
    renderElderlyTrendChart();
    // Summary 카드 업데이트를 위해 ratio TOP5를 함께 쓰므로,
    // 여기서는 차트만 그리고 summary는 loadTop5Tables() 안에서 처리
  } catch (err) {
    console.error("노인 인구 추세 로딩 실패:", err);
    alert("노인 인구 추세 데이터를 불러오지 못했습니다.");
  }
}

// 메인 노인 인구 차트 렌더링
function renderElderlyTrendChart() {
  const canvas = document.getElementById("dashboard-chart");
  if (!canvas || !elderlyMainTrend) return;

  const ctx = canvas.getContext("2d");

  // X축: 연도 배열
  const years = elderlyMainTrend.map((item) => item.year);
  const totalSeries = elderlyMainTrend.map((item) => ({
    x: item.year,
    y: item.total_elderly_population || 0
  }));

  const datasets = [];

  // 0) 전체 합계 라인
  if (showTotal) {
    datasets.push(
      createLineDataset("서울 전체 노인 인구", totalSeries, "#4e73df", false)
    );
  }

  // 1) 선택된 구별 라인들
  selectedRegions.forEach((region) => {
    const series = regionSeriesCache[region];
    if (!series) return;

    // series: [ {year, value}, ... ] 를 Chart.js용으로 변환
    const data = series.map((row) => ({
      x: row.year,
      y: row.value
    }));

    datasets.push(
      createLineDataset(region, data, getColorForRegion(region), true)
    );
  });

  const config = {
    type: "line",
    data: {
      labels: years,
      datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "linear",
          title: { display: true, text: "연도" },
          ticks: {
            callback: (value) => `${value}`
          }
        },
        y: {
          title: { display: true, text: "노인 인구" }
        }
      },
      plugins: {
        legend: {
          position: "bottom"
        },
        tooltip: {
          mode: "index",
          intersect: false,
          callbacks: {
            label: (context) => {
              const label = context.dataset.label || "";
              const val = context.parsed.y || 0;
              return `${label}: ${val.toLocaleString("ko-KR")}`;
            }
          }
        }
      }
    }
  };

  if (dashboardChart) {
    dashboardChart.destroy();
  }
  dashboardChart = new Chart(ctx, config);
}

// ------------------------------
// 3) 구 체크박스 & 구별 라인
// ------------------------------
function initRegionCheckboxes() {
  const container = document.getElementById("region-checkbox-container");
  if (!container) return;

  container.innerHTML = "";

  // 0) 전체(서울 합계) 체크박스
  const allWrapper = document.createElement("div");
  allWrapper.className = "form-check form-check-inline mb-1 me-3";

  const allInput = document.createElement("input");
  allInput.type = "checkbox";
  allInput.className = "form-check-input";
  allInput.id = "chk-region-all";
  allInput.checked = true;
  allInput.addEventListener("change", (e) => {
    showTotal = e.target.checked;
    renderElderlyTrendChart();
  });

  const allLabel = document.createElement("label");
  allLabel.className = "form-check-label";
  allLabel.setAttribute("for", "chk-region-all");
  allLabel.textContent = "서울 전체";

  allWrapper.appendChild(allInput);
  allWrapper.appendChild(allLabel);
  container.appendChild(allWrapper);

  // 1) 서울 25개 구 체크박스
  SEOUL_REGIONS.forEach((name) => {
    const id = `chk-region-${name}`;

    const wrapper = document.createElement("div");
    wrapper.className = "form-check form-check-inline mb-1";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.className = "form-check-input";
    input.id = id;
    input.value = name;
    input.addEventListener("change", onRegionCheckboxChange);

    const label = document.createElement("label");
    label.className = "form-check-label";
    label.setAttribute("for", id);
    label.textContent = name;

    wrapper.appendChild(input);
    wrapper.appendChild(label);
    container.appendChild(wrapper);
  });
}
function initLonelyRegionCheckboxes() {
  const container = document.getElementById("lonely-region-checkbox-container");
  if (!container) return;

  container.innerHTML = "";

  // 0) 전체(서울 25개 구 합계) 체크박스
  const allWrapper = document.createElement("div");
  allWrapper.className = "form-check form-check-inline mb-1 me-3";

  const allInput = document.createElement("input");
  allInput.type = "checkbox";
  allInput.className = "form-check-input";
  allInput.id = "chk-lonely-all";
  allInput.checked = true;

  allInput.addEventListener("change", (e) => {
    showLonelyTotal = e.target.checked;
    rebuildLonelyTrendChart();
  });

  const allLabel = document.createElement("label");
  allLabel.className = "form-check-label fw-bold";
  allLabel.setAttribute("for", "chk-lonely-all");
  allLabel.textContent = "서울 전체";

  allWrapper.appendChild(allInput);
  allWrapper.appendChild(allLabel);
  container.appendChild(allWrapper);

  // 1) 25개 구 체크박스
  SEOUL_REGIONS.forEach((name) => {
    const id = `chk-lonely-region-${name}`;

    const wrapper = document.createElement("div");
    wrapper.className = "form-check form-check-inline mb-1";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.className = "form-check-input";
    input.id = id;
    input.value = name;

    input.addEventListener("change", onLonelyRegionCheckboxChange);

    const label = document.createElement("label");
    label.className = "form-check-label";
    label.setAttribute("for", id);
    label.textContent = name;

    wrapper.appendChild(input);
    wrapper.appendChild(label);
    container.appendChild(wrapper);
  });
}

// 체크박스 change 핸들러
async function onRegionCheckboxChange(event) {
  const region = event.target.value;

  if (event.target.checked) {
    selectedRegions.add(region);

    // 캐시에 없으면 API로 한 번만 조회
    if (!regionSeriesCache[region]) {
      try {
        const json = await fetchJson(
          `/api/elderly/forecast/${encodeURIComponent(region)}`
        );
        const data = json.data || json; // { region, history, forecast, message }

        const history = data.history || [];
        const forecast = data.forecast || [];

        if (!history.length && !forecast.length) {
          throw new Error("실측/예측 데이터가 없습니다.");
        }

        const combined = [...history, ...forecast]
          .sort((a, b) => a.year - b.year)
          .map((row) => ({
            year: row.year,
            value: row.value
          }));

        regionSeriesCache[region] = combined;
      } catch (err) {
        console.warn("구 예측 시리즈 로딩 실패:", region, err);
        alert(`[${region}] 예측 데이터를 불러오지 못했습니다.\n${err.message}`);
        selectedRegions.delete(region);
        event.target.checked = false;
        return;
      }
    }
  } else {
    selectedRegions.delete(region);
  }

  renderElderlyTrendChart();
}

async function onLonelyRegionCheckboxChange(event) {
  const region = event.target.value;

  if (event.target.checked) {
    selectedLonelyRegions.add(region);

    // 캐시에 없으면 API에서 한 번만 가져오기
    if (!lonelyRegionSeriesCache[region]) {
      try {
        const url = `/api/lonely/forecast?region=${encodeURIComponent(region)}`;
        const res = await fetch(url);
        const json = await res.json();

        if (!res.ok || (json.status && json.status.toLowerCase() === "error")) {
          console.warn("lonely forecast API error:", region, json);
          alert(`[${region}] 고독사 예측 데이터를 불러오지 못했습니다.`);
          selectedLonelyRegions.delete(region);
          event.target.checked = false;
          return;
        }

        const payload = json.data || json;
        const history = payload.history || [];
        const forecast = payload.forecast || [];
        const all = [...history, ...forecast].sort((a, b) => a.year - b.year);

        // [{year, value}, ...]
        lonelyRegionSeriesCache[region] = all;
      } catch (err) {
        console.error("lonely forecast fetch error:", err);
        alert(`[${region}] 고독사 예측 데이터를 불러오지 못했습니다.`);
        selectedLonelyRegions.delete(region);
        event.target.checked = false;
        return;
      }
    }
  } else {
    selectedLonelyRegions.delete(region);
  }

  rebuildLonelyTrendChart();
}


// ------------------------------
// 4) 고독사 추세 (메인 차트)
// ------------------------------
async function loadLonelyTrend() {
  try {
    const json = await fetchJson(
      "/api/lonely/trend?start_year=2017&end_year=2035"
    );
    const items = json.items || json.data || [];

    const canvas = document.getElementById("lonely-chart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    // history / forecast 분리
    const history = items.filter((x) => (x.is_forecast || "N") === "N");
    const forecast = items.filter((x) => (x.is_forecast || "N") === "Y");

    const historyData = history.map((x) => ({ x: x.year, y: x.value }));
    const forecastData = forecast.map((x) => ({ x: x.year, y: x.value }));

    const datasets = [];
    if (historyData.length) {
      datasets.push(
        createLineDataset("실측 고독사 수", historyData, "#e74a3b", false)
      );
    }
    if (forecastData.length) {
      datasets.push(
        createLineDataset("예측 고독사 수", forecastData, "#f6c23e", true)
      );
    }

    const labels = items.map((i) => i.year);

    const config = {
      type: "line",
      data: {
        labels,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: "linear",
            title: { display: true, text: "연도" }
          },
          y: {
            title: { display: true, text: "고독사 수" }
          }
        },
        plugins: {
          legend: {
            position: "bottom"
          },
          tooltip: {
            mode: "index",
            intersect: false,
            callbacks: {
              label: (ctx) => {
                const label = ctx.dataset.label || "";
                const val = ctx.parsed.y || 0;
                return `${label}: ${val.toLocaleString("ko-KR")}`;
              }
            }
          }
        }
      }
    };

    if (lonelyChart) {
      lonelyChart.destroy();
    }
    lonelyChart = new Chart(ctx, config);
  } catch (err) {
    console.error("고독사 추세 로딩 실패:", err);
    alert("고독사 추세 데이터를 불러오지 못했습니다.");
  }
}

// ------------------------------
// 5) TOP5 테이블 (4종)
// ------------------------------
async function loadTop5Tables() {
  try {
    // 노인 인구 증가율 TOP5
    const elderlyRatioJson = await fetchJson(
      "/api/elderly/top5?base_year=2023&target_year=2035&by=ratio"
    );
    const elderlyRatioItems = elderlyRatioJson.items || elderlyRatioJson.data || [];
    renderTop5Table(
      "population-growth-body",
      elderlyRatioItems,
      (row) => row.region,
      (row) => (row.metric_value * 100).toFixed(1) // 0.35 → 35.0
    );

    // Summary 카드: 최신 총 인구 + 증가율 TOP/Bottom
    renderSummaryFromTrendAndTop(elderlyMainTrend, elderlyRatioItems);

    // 노인 인구 TOP5 (2050년 인구 기준)
    const elderlyAbsJson = await fetchJson(
      "/api/elderly/top5?base_year=2023&target_year=2035&by=absolute"
    );
    const elderlyAbsItems = elderlyAbsJson.items || elderlyAbsJson.data || [];
    renderTop5Table(
      "population-count-body",
      elderlyAbsItems,
      (row) => row.region,
      (row) => (row.target_value || 0).toLocaleString("ko-KR")
    );

    // 고독사 증가율 TOP5
    const lonelyRatioJson = await fetchJson(
      "/api/lonely/top5?base_year=2023&target_year=2035&by=ratio"
    );
    const lonelyRatioItems = lonelyRatioJson.items || lonelyRatioJson.data || [];
    renderTop5Table(
      "lonely-growth-body",
      lonelyRatioItems,
      (row) => row.region,
      (row) => (row.metric_value * 100).toFixed(1)
    );

    // 고독사 수 TOP5 (2050년 값 기준)
    const lonelyAbsJson = await fetchJson(
      "/api/lonely/top5?base_year=2023&target_year=2035&by=absolute"
    );
    const lonelyAbsItems = lonelyAbsJson.items || lonelyAbsJson.data || [];
    renderTop5Table(
      "lonely-count-body",
      lonelyAbsItems,
      (row) => row.region,
      (row) => (row.target_value || 0).toLocaleString("ko-KR")
    );
  } catch (err) {
    console.error("TOP5 데이터 로딩 실패:", err);
    alert("TOP5 데이터를 불러오는 중 오류가 발생했습니다.");
  }
}

// 공통 TOP5 렌더 함수
function renderTop5Table(tbodyId, items, regionGetter, valueFormatter) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;

  tbody.innerHTML = "";

  if (!items || !items.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 3;
    td.className = "text-center text-muted";
    td.textContent = "데이터 없음";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  items.forEach((row, idx) => {
    const tr = document.createElement("tr");

    const tdRank = document.createElement("td");
    tdRank.textContent = idx + 1;

    const tdRegion = document.createElement("td");
    tdRegion.textContent = regionGetter(row);

    const tdValue = document.createElement("td");
    tdValue.className = "text-end";
    tdValue.textContent = valueFormatter(row);

    tr.appendChild(tdRank);
    tr.appendChild(tdRegion);
    tr.appendChild(tdValue);
    tbody.appendChild(tr);
  });
}

// Summary 카드: 전체 추세 + 증가율 TOP5 기반
function renderSummaryFromTrendAndTop(trendItems, ratioTop5) {
  const totalEl = document.getElementById("summary-total");
  const topEl = document.getElementById("summary-growth-top");
  const bottomEl = document.getElementById("summary-growth-bottom");
  if (!totalEl || !topEl || !bottomEl) return;

  // 최신 연도 총 노인 인구
  if (trendItems && trendItems.length) {
    const last = trendItems[trendItems.length - 1];
    const total = last.total_elderly_population || 0;
    totalEl.textContent = total.toLocaleString("ko-KR");
  } else {
    totalEl.textContent = "-";
  }

  // 증가율 TOP / BOTTOM 구
  if (ratioTop5 && ratioTop5.length) {
    // TOP1
    const topRow = ratioTop5[0];
    topEl.textContent = `${topRow.region} (${(topRow.metric_value * 100).toFixed(1)}%)`;

    // BOTTOM은 서버에서 따로 주지 않는다고 가정 → metric_value 기준 오름차순 정렬 후 첫 번째
    const sorted = [...ratioTop5].sort((a, b) => a.metric_value - b.metric_value);
    const bottomRow = sorted[0];
    bottomEl.textContent = `${bottomRow.region} (${(bottomRow.metric_value * 100).toFixed(1)}%)`;
  } else {
    topEl.textContent = "-";
    bottomEl.textContent = "-";
  }
}

// ------------------------------
// 6) 예측 모달 (노인 인구 / 고독사)
// ------------------------------
function bindForecastButtons() {
  const elderlyBtn = document.getElementById("btn-load-forecast");
  const elderlyInput = document.getElementById("forecast-region-input");
  const lonelyBtn = document.getElementById("btn-load-lonely-forecast");
  const lonelyInput = document.getElementById("lonely-forecast-region-input");

  if (elderlyBtn && elderlyInput) {
    elderlyBtn.addEventListener("click", () => {
      const region = elderlyInput.value.trim();
      if (!region) {
        alert("구 이름을 입력하세요. (예: 강남구)");
        return;
      }
      openElderlyForecastModal(region);
    });

    elderlyInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        elderlyBtn.click();
      }
    });
  }

  if (lonelyBtn && lonelyInput) {
    lonelyBtn.addEventListener("click", () => {
      const region = lonelyInput.value.trim();
      if (!region) {
        alert("구 이름을 입력하세요. (예: 강남구)");
        return;
      }
      openLonelyForecastModal(region);
    });

    lonelyInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        lonelyBtn.click();
      }
    });
  }
}

// 노인 인구 예측 모달
async function openElderlyForecastModal(region) {
  try {
    const json = await fetchJson(
      `/api/elderly/forecast/${encodeURIComponent(region)}`
    );
    const data = json.data || json;

    const modalTitle = document.getElementById("forecast-modal-title");
    const modalMsg = document.getElementById("forecast-modal-message");
    const tbody = document.getElementById("forecast-modal-body");
    const canvas = document.getElementById("forecast-chart");

    if (!modalTitle || !modalMsg || !tbody || !canvas) return;

    modalTitle.textContent = `${data.region} 노인 인구 실측/예측`;
    modalMsg.textContent = data.message || "";

    const history = data.history || [];
    const forecast = data.forecast || [];

    // 테이블 렌더
    tbody.innerHTML = "";
    const rows = [
      ...history.map((x) => ({ ...x, kind: "실측" })),
      ...forecast.map((x) => ({ ...x, kind: "예측" }))
    ].sort((a, b) => a.year - b.year);

    if (!rows.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 3;
      td.className = "text-center text-muted";
      td.textContent = "데이터 없음";
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      rows.forEach((row) => {
        const tr = document.createElement("tr");

        const tdYear = document.createElement("td");
        tdYear.textContent = row.year;

        const tdVal = document.createElement("td");
        tdVal.className = "text-end";
        tdVal.textContent = (row.value || 0).toLocaleString("ko-KR");

        const tdKind = document.createElement("td");
        tdKind.textContent = row.kind;

        tr.appendChild(tdYear);
        tr.appendChild(tdVal);
        tr.appendChild(tdKind);
        tbody.appendChild(tr);
      });
    }

    // 차트 렌더
    const ctx = canvas.getContext("2d");
    const historyData = history.map((x) => ({ x: x.year, y: x.value }));
    const forecastData = forecast.map((x) => ({ x: x.year, y: x.value }));

    const datasets = [];
    if (historyData.length) {
      datasets.push(
        createLineDataset("실측", historyData, "#1cc88a", false)
      );
    }
    if (forecastData.length) {
      datasets.push(
        createLineDataset("예측", forecastData, "#36b9cc", true)
      );
    }

    const labels = [...history, ...forecast].map((x) => x.year);

    const config = {
      type: "line",
      data: {
        labels,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { type: "linear", title: { display: true, text: "연도" } },
          y: { title: { display: true, text: "노인 인구" } }
        },
        plugins: {
          legend: { position: "bottom" }
        }
      }
    };

    if (forecastChart) {
      forecastChart.destroy();
    }
    forecastChart = new Chart(ctx, config);

    // Bootstrap 모달 열기
    const modalEl = document.getElementById("forecastModal");
    if (modalEl) {
      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
  } catch (err) {
    console.error("노인 인구 예측 모달 오류:", err);
    alert(`[${region}] 노인 인구 예측 데이터를 불러오지 못했습니다.\n${err.message}`);
  }
}

// 고독사 예측 모달
async function openLonelyForecastModal(region) {
  try {
    const json = await fetchJson(
      `/api/lonely/forecast?region=${encodeURIComponent(region)}`
    );
    const data = json.data || json;

    const modalTitle = document.getElementById("lonelyForecastLabel");
    const modalMsg = document.getElementById("lonely-forecast-message");
    const tbody = document.getElementById("lonely-forecast-body");
    const canvas = document.getElementById("lonelyForecastChart");

    if (!modalTitle || !modalMsg || !tbody || !canvas) return;

    modalTitle.textContent = `${data.region} 고독사 실측/예측`;
    modalMsg.textContent = data.message || "";

    const history = data.history || [];
    const forecast = data.forecast || [];

    // 테이블 렌더
    tbody.innerHTML = "";
    const rows = [
      ...history.map((x) => ({ ...x, kind: "실측" })),
      ...forecast.map((x) => ({ ...x, kind: "예측" }))
    ].sort((a, b) => a.year - b.year);

    if (!rows.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 3;
      td.className = "text-center text-muted";
      td.textContent = "데이터 없음";
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      rows.forEach((row) => {
        const tr = document.createElement("tr");

        const tdYear = document.createElement("td");
        tdYear.textContent = row.year;

        const tdVal = document.createElement("td");
        tdVal.className = "text-end";
        tdVal.textContent = (row.value || 0).toLocaleString("ko-KR");

        const tdKind = document.createElement("td");
        tdKind.textContent = row.kind;

        tr.appendChild(tdYear);
        tr.appendChild(tdVal);
        tr.appendChild(tdKind);
        tbody.appendChild(tr);
      });
    }

    // 차트 렌더
    const ctx = canvas.getContext("2d");
    const historyData = history.map((x) => ({ x: x.year, y: x.value }));
    const forecastData = forecast.map((x) => ({ x: x.year, y: x.value }));

    const datasets = [];
    if (historyData.length) {
      datasets.push(
        createLineDataset("실측", historyData, "#e74a3b", false)
      );
    }
    if (forecastData.length) {
      datasets.push(
        createLineDataset("예측", forecastData, "#f6c23e", true)
      );
    }

    const labels = [...history, ...forecast].map((x) => x.year);

    const config = {
      type: "line",
      data: {
        labels,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { type: "linear", title: { display: true, text: "연도" } },
          y: { title: { display: true, text: "고독사 수" } }
        },
        plugins: {
          legend: { position: "bottom" }
        }
      }
    };

    if (lonelyForecastChart) {
      lonelyForecastChart.destroy();
    }
    lonelyForecastChart = new Chart(ctx, config);

    // Bootstrap 모달 열기
    const modalEl = document.getElementById("lonelyForecastModal");
    if (modalEl) {
      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
  } catch (err) {
    console.error("고독사 예측 모달 오류:", err);
    alert(`[${region}] 고독사 예측 데이터를 불러오지 못했습니다.\n${err.message}`);
  }
}
