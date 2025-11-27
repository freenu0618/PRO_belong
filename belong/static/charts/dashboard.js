// =======================================
// 대시보드 스크립트 (요약 + 차트 + TOP5 + 예측 모달)
// =======================================

// 전역 차트 핸들
let dashboardChart = null;
let forecastChart = null;

// 기본 색상
const TOTAL_COLOR = "#4e73df";

// 구별 색상: region 이름으로 HSL 색상 생성
function getColorForRegion(region) {
  // 간단한 해시 → 0~360
  let hash = 0;
  for (let i = 0; i < region.length; i++) {
    hash = region.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  // 채도, 명도는 고정
  return `hsl(${hue}, 65%, 50%)`;
}

// 🔹 노인 인구 전체 추세 + 구별 예측 캐시
let elderlyMainTrend = [];               // /api/elderly/trend 데이터
const selectedRegions = new Set();       // 체크된 구
const regionSeriesCache = {};
// 대시보드 기준 연도 (TOP5 계산용)
const DASHBOARD_BASE_YEAR = 2023;
const DASHBOARD_TARGET_YEAR = 2050;

// 🔹 서울 25개 구 이름 목록 (체크박스 생성용)
const SEOUL_REGIONS = [
  "강남구", "강동구", "강북구", "강서구", "관악구",
  "광진구", "구로구", "금천구", "노원구", "도봉구",
  "동대문구", "동작구", "마포구", "서대문구", "서초구",
  "성동구", "성북구", "송파구", "양천구", "영등포구",
  "용산구", "은평구", "종로구", "중구", "중랑구",
];
// 공통 fetch 헬퍼
async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`Request failed: ${res.status} ${url}`);
    }
    return await res.json();
}

// =========================
// 1) 노인 인구 추세 / TOP5 / 스냅샷 API 래퍼
// =========================

// 1-1) 전체 노인 인구 추세 (2017~2050)
async function fetchElderlyTrend(startYear = 2017, endYear = 2050) {
    const data = await fetchJson(`/api/elderly/trend?start_year=${startYear}&end_year=${endYear}`);
    return data.items || [];
}
let showTotal = true;  // 전체 추세 표시 여부

function initRegionCheckboxes() {
  const container = document.getElementById("region-checkbox-container");
  if (!container) return;

  container.innerHTML = "";

  // ✅ 0) 전체(서울 25개 구 합계) 체크박스
  const allWrapper = document.createElement("div");
  allWrapper.className = "form-check form-check-inline mb-1 me-3";

  const allInput = document.createElement("input");
  allInput.type = "checkbox";
  allInput.className = "form-check-input";
  allInput.id = "chk-region-all";
  allInput.checked = true;           // 기본 ON
  allInput.addEventListener("change", (e) => {
    showTotal = e.target.checked;
    rebuildDashboardChart();
  });

  const allLabel = document.createElement("label");
  allLabel.className = "form-check-label fw-bold";
  allLabel.setAttribute("for", "chk-region-all");
  allLabel.textContent = "서울 전체";

  allWrapper.appendChild(allInput);
  allWrapper.appendChild(allLabel);
  container.appendChild(allWrapper);

  // ✅ 1) 25개 구 체크박스
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


async function onRegionCheckboxChange(event) {
  const region = event.target.value;

  if (event.target.checked) {
    selectedRegions.add(region);

    // 캐시에 없으면 API에서 한 번만 가져오기
    if (!regionSeriesCache[region]) {
      try {
        const res = await fetch(`/api/elderly/forecast/${encodeURIComponent(region)}`);
        const json = await res.json();

        if (!res.ok || (json.status && json.status.toLowerCase() === "error")) {
          console.warn("forecast API error for region:", region, json);
          alert(`[${region}] 예측 데이터를 불러오지 못했습니다.`);
          selectedRegions.delete(region);
          event.target.checked = false;
          return;
        }

        const payload = json.data || json;
        const history = payload.history || [];
        const forecast = payload.forecast || [];

        const all = [...history, ...forecast].sort((a, b) => a.year - b.year);
        regionSeriesCache[region] = all;   // [{year, value}, ...]
      } catch (err) {
        console.error("forecast fetch error:", err);
        alert(`[${region}] 예측 데이터를 불러오지 못했습니다.`);
        selectedRegions.delete(region);
        event.target.checked = false;
        return;
      }
    }
  } else {
    selectedRegions.delete(region);
  }

  // 그래프 다시 그리기
  rebuildDashboardChart();
}
function rebuildDashboardChart() {
  if (!elderlyMainTrend.length) return;

  const labels = elderlyMainTrend.map(d => d.year);
  const baseValues = elderlyMainTrend.map(d => d.total_elderly_population);

  const datasets = [];

  // ✅ 전체 추세는 showTotal 이 true일 때만 추가
  if (showTotal) {
    datasets.push({
      label: "서울 25개 구 노인 인구(전체)",
      data: baseValues,
      borderColor: TOTAL_COLOR,
      backgroundColor: "rgba(78, 115, 223, 0.08)",
      tension: 0.15,
      fill: false,
      borderWidth: 3,
      pointRadius: 2,
    });
  }

  // ✅ 선택된 각 구에 대해 dataset 추가
  selectedRegions.forEach((region) => {
    const series = regionSeriesCache[region];
    if (!series) return;

    const map = new Map(series.map(d => [d.year, d.value]));
    const data = labels.map(year => map.get(year) ?? null);

    datasets.push({
      label: region,
      data,
      borderColor: getColorForRegion(region),  // 🔴 개별 색상
      tension: 0.25,
      fill: false,
      borderWidth: 2,
      pointRadius: 0,
    });
  });

  const canvas = document.getElementById("dashboard-chart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  if (dashboardChart) {
    dashboardChart.data.labels = labels;
    dashboardChart.data.datasets = datasets;
    dashboardChart.update();
  } else {
    dashboardChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "nearest",
          intersect: false,
        },
        plugins: {
          legend: { position: "top" },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const v = ctx.parsed.y;
                if (v == null) return "";
                return `${ctx.dataset.label}: ${v.toLocaleString("ko-KR")}명`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "연도" },
          },
          y: {
            title: { display: true, text: "노인 인구 수" },
            beginAtZero: true,
            ticks: {
              callback: (v) => v.toLocaleString("ko-KR") + "명",
            },
          },
        },
      },
    });
  }
}


// 1-2) 증가 TOP5 (증가율 / 증가 인원수)
async function fetchElderlyTop5(baseYear, targetYear, by) {
    const params = new URLSearchParams({
        base_year: baseYear,
        target_year: targetYear,
        by
    });
    const data = await fetchJson(`/api/elderly/top5?${params.toString()}`);
    return data.items || [];
}

// 1-3) 특정 연도 구별 스냅샷 (필요시 확장용 – 현재는 여기선 안 씀)
async function fetchElderlyRegions(year) {
    const data = await fetchJson(`/api/elderly/regions?year=${year}`);
    return data.items || [];
}

// =========================
// 2) Summary 카드 렌더링
//    - 총 노인 인구: targetYear(예: 2050) 전체 합
//    - 증가 TOP 구 / 증가율 최하위 구: ratio TOP5 기준 상/하위
// =========================
function renderSummaryFromTrendAndTop(trendItems, ratioTop5) {
    const totalEl = document.getElementById("summary-total");
    const topEl = document.getElementById("summary-growth-top");
    const bottomEl = document.getElementById("summary-growth-bottom");

    if (!totalEl || !topEl || !bottomEl) return;

    // 총 노인 인구: 추세 마지막 연도 값
    if (trendItems && trendItems.length) {
        const last = trendItems[trendItems.length - 1];
        const total = last.total_elderly_population || 0;
        totalEl.textContent = total.toLocaleString("ko-KR");
    } else {
        totalEl.textContent = "-";
    }

    // 증가 TOP 구 / 최하위 구: ratioTop5와 그 반대
    if (ratioTop5 && ratioTop5.length) {
        // ratioTop5는 이미 metric_value 내림차순 TOP5라서
        const topRegion = ratioTop5[0]?.region || "-";
        topEl.textContent = topRegion;
    } else {
        topEl.textContent = "-";
    }

    // 최하위 구는 전체 증가율 중 제일 낮은 구여야 해서,
    // ratioTop5 에 없는 구들은 별도 계산이 필요하지만,
    // 일단 TOP5 안에서만 최하위를 보여주는 버전으로 두고
    // 필요하면 나중에 전체 구 기준으로 확장할 수 있음.
    if (ratioTop5 && ratioTop5.length) {
        const bottomRegion = ratioTop5[ratioTop5.length - 1]?.region || "-";
        bottomEl.textContent = bottomRegion;
    } else {
        bottomEl.textContent = "-";
    }
}

// =========================
// 3) TOP5 테이블 렌더링
//      - 왼쪽: 증가율 TOP5 (ratio)
//      - 오른쪽: 인구 수 TOP5 (absolute)
// =========================
function renderTopTablesFromApis(ratioItems, absoluteItems) {
    const growthBody = document.getElementById("population-growth-body");
    const countBody = document.getElementById("population-count-body");
    if (!growthBody || !countBody) return;

    growthBody.innerHTML = "";
    countBody.innerHTML = "";

    // ratioItems: metric_value = 증가율 (0.35 → 35%)
    ratioItems.forEach(row => {
        const latest = row.target_value || 0;
        const rate = (row.metric_value || 0) * 100; // %
        growthBody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${latest.toLocaleString("ko-KR")}</td>
                <td>${rate.toFixed(2)}%</td>
            </tr>
        `;
    });

    // absoluteItems: metric_value = 증가 인원수
    // 표 헤더는 "독거노인 인구 TOP5 / 증가율(%)" 이라서,
    // 여기서는 증가 인원수 + 증가율을 같이 보여준다.
    absoluteItems.forEach(row => {
        const latest = row.target_value || 0;
        const diff = row.diff || 0;
        let ratePercent = 0;
        if (row.base_value) {
            ratePercent = (diff / row.base_value) * 100;
        }
        countBody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${latest.toLocaleString("ko-KR")}</td>
                <td>${ratePercent.toFixed(2)}%</td>
            </tr>
        `;
    });
}

// =========================
// 4) 메인 라인 차트 (전체 노인 인구 추세)
//    - /api/elderly/trend 사용
//    - 실측 / 예측을 다른 스타일로 표시
// =========================
async function renderElderlyTrendChart() {
  const items = await fetchElderlyTrend(2017, 2050);
  if (!items.length) return;

  elderlyMainTrend = items;
  rebuildDashboardChart();
}


// =========================
// 5) 예측 버튼 클릭 핸들러 (/api/elderly/forecast/<region>)
//    기존 코드 그대로 유지 (이미 동작 중이면 손댈 필요 X)
// =========================
async function handleForecastClick() {
    const input = document.getElementById("forecast-region-input");
    if (!input) {
        console.error("forecast-region-input 요소를 찾을 수 없습니다.");
        return;
    }

    const region = input.value.trim();
    if (!region) {
        alert("구 이름을 입력해 주세요. (예: 강남구)");
        input.focus();
        return;
    }

    const url = `/api/elderly/forecast/${encodeURIComponent(region)}`;
    console.log("[Forecast] 요청 URL:", url);

    let res;
    try {
        res = await fetch(url);
    } catch (err) {
        console.error("[Forecast] fetch 실패:", err);
        alert("예측 데이터를 불러오지 못했습니다. 네트워크 상태를 확인해 주세요.");
        return;
    }

    let json;
    try {
        json = await res.json();
    } catch (err) {
        console.error("[Forecast] JSON 파싱 실패:", err);
        alert("예측 데이터를 불러오지 못했습니다. 서버 응답 형식을 확인해 주세요.");
        return;
    }

    console.log("[Forecast] 응답:", res.status, json);

    if (!res.ok) {
        const msg =
            (json && json.message) ||
            `예측 API 호출 실패 (HTTP ${res.status})`;
        openForecastModal(region, {
            message: msg,
            history: [],
            forecast: [],
        });
        return;
    }

    if (json.status && json.status.toLowerCase() === "error") {
        const msg = json.message || "예측 데이터를 찾을 수 없습니다.";
        openForecastModal(region, {
            message: msg,
            history: [],
            forecast: [],
        });
        return;
    }

    const payload = json.data || json;
    try {
        openForecastModal(region, payload);
    } catch (err) {
        console.error("[Forecast] 모달 렌더링 실패:", err);
        alert("예측 결과를 화면에 표시하는 중 오류가 발생했습니다. 콘솔 로그를 확인해 주세요.");
    }
}

// =========================
// 6) 예측 모달 & 차트
// =========================
function openForecastModal(region, data) {
    const modalEl = document.getElementById("forecastModal");
    const titleEl = document.getElementById("forecastModalLabel");
    const msgEl = document.getElementById("forecast-modal-message");
    const tbody = document.getElementById("forecast-modal-body");

    if (!modalEl || !titleEl || !tbody) {
        const history = (data.history || []).map(d => `${d.year}: ${d.value}`).join("\n");
        const forecast = (data.forecast || []).map(d => `${d.year}: ${d.value}`).join("\n");
        alert(
            `[${region}] 예측 결과\n\n` +
            (data.message ? data.message + "\n\n" : "") +
            (history ? "실측\n" + history + "\n\n" : "") +
            (forecast ? "예측\n" + forecast : "")
        );
        return;
    }

    titleEl.innerText = `[${region}] 예측 결과`;
    if (msgEl) {
        msgEl.innerText = data.message || "";
    }

    tbody.innerHTML = "";

    (data.history || []).forEach(item => {
        tbody.innerHTML += `
            <tr>
                <td>실측</td>
                <td>${item.year}</td>
                <td>${(item.value ?? 0).toLocaleString("ko-KR")}</td>
            </tr>
        `;
    });

    (data.forecast || []).forEach(item => {
        tbody.innerHTML += `
            <tr class="table-warning">
                <td>예측</td>
                <td>${item.year}</td>
                <td>${(item.value ?? 0).toLocaleString("ko-KR")}</td>
            </tr>
        `;
    });

    try {
        renderForecastChart(data);
    } catch (err) {
        console.error("[Forecast] 차트 렌더링 실패:", err);
    }

    if (window.bootstrap && bootstrap.Modal) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    } else {
        modalEl.style.display = "block";
    }
}

function renderForecastChart(data) {
    const canvas = document.getElementById("forecast-chart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const history = data.history || [];
    const forecast = data.forecast || [];

    if (!history.length && !forecast.length) {
        if (forecastChart) {
            forecastChart.destroy();
            forecastChart = null;
        }
        return;
    }

    const yearsSet = new Set();
    history.forEach(d => yearsSet.add(d.year));
    forecast.forEach(d => yearsSet.add(d.year));
    const years = Array.from(yearsSet).sort((a, b) => a - b);

    const historyMap = new Map(history.map(d => [d.year, d.value]));
    const forecastMap = new Map(forecast.map(d => [d.year, d.value]));

    const historySeries = years.map(y => historyMap.has(y) ? historyMap.get(y) : null);
    const forecastSeries = years.map(y => forecastMap.has(y) ? forecastMap.get(y) : null);

    if (forecastChart) {
        forecastChart.destroy();
    }

    forecastChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: years,
            datasets: [
                {
                    label: "실측",
                    data: historySeries,
                    borderWidth: 2,
                    tension: 0.2,
                },
                {
                    label: "예측",
                    data: forecastSeries,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.2,
                },
            ],
        },
        options: {
            responsive: true,
            interaction: {
                mode: "nearest",
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: "bottom",
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || "";
                            const value = context.parsed.y;
                            if (value == null) return "";
                            return `${label}: ${value.toLocaleString("ko-KR")}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    title: { display: true, text: "연도" },
                },
                y: {
                    title: { display: true, text: "노인 인구 수" },
                    beginAtZero: true,
                },
            },
        },
    });
}
// 고독사 추세용
async function fetchLonelyTrend(startYear = 2017, endYear = 2050) {
  const data = await fetchJson(`/api/lonely/trend?start_year=${startYear}&end_year=${endYear}`);
  return data.items || [];
}

let lonelyChart = null;

async function renderLonelyTrendChart() {
  const items = await fetchLonelyTrend(2017, 2050);
  if (!items.length) return;

  const labels = items.map(d => d.year);
  const values = items.map(d => d.value);
  const borderStyles = items.map(d => (d.is_forecast ? [5, 5] : [])); // 필요하면 응용

  const canvas = document.getElementById("lonely-chart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  if (lonelyChart) lonelyChart.destroy();

  lonelyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "서울 25개 구 고독사 인원",
          data: values,
          borderColor: "#e74a3b",
          backgroundColor: "rgba(231, 74, 59, 0.08)",
          tension: 0.15,
          fill: false,
          borderWidth: 3,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v = ctx.parsed.y;
              if (v == null) return "";
              const item = items[ctx.dataIndex];
              const suffix = item.is_forecast ? " (예측)" : " (실측)";
              return ctx.dataset.label + suffix + ": " + v.toLocaleString("ko-KR") + "명";
            },
          },
        },
      },
      scales: {
        x: { title: { display: true, text: "연도" } },
        y: {
          title: { display: true, text: "고독사 인원 수" },
          beginAtZero: true,
          ticks: { callback: (v) => v.toLocaleString("ko-KR") + "명" },
        },
      },
    },
  });
}

async function fetchLonelyTop5(baseYear, targetYear, by) {
  const params = new URLSearchParams({
    base_year: baseYear,
    target_year: targetYear,
    by,
  });
  const data = await fetchJson(`/api/lonely/top5?${params.toString()}`);
  return data.items || [];
}

function renderLonelyTopTables(ratioItems, absoluteItems) {
  const growthBody = document.getElementById("lonely-growth-body");
  const countBody = document.getElementById("lonely-count-body");
  if (!growthBody || !countBody) return;

  growthBody.innerHTML = "";
  countBody.innerHTML = "";

  ratioItems.forEach((row) => {
    const latest = row.target_value || 0;
    const rate = (row.metric_value || 0) * 100;
    growthBody.innerHTML += `
      <tr>
        <td>${row.region}</td>
        <td>${latest.toLocaleString("ko-KR")}</td>
        <td>${rate.toFixed(2)}%</td>
      </tr>
    `;
  });

  absoluteItems.forEach((row) => {
    const latest = row.target_value || 0;
    const diff = row.diff || 0;
    let ratePercent = 0;
    if (row.base_value) {
      ratePercent = (diff / row.base_value) * 100;
    }
    countBody.innerHTML += `
      <tr>
        <td>${row.region}</td>
        <td>${latest.toLocaleString("ko-KR")}</td>
        <td>${ratePercent.toFixed(2)}%</td>
      </tr>
    `;
  });
}

// =========================
// 7) 초기화
// =========================
async function initDashboard() {
    try {
        // 1) 추세 차트
        const trendPromise = renderElderlyTrendChart();

        // 2) TOP5 + Summary (동시에 필요한 데이터들)
        const [ratioTop5, absoluteTop5, trendItems] = await Promise.all([
            fetchElderlyTop5(DASHBOARD_BASE_YEAR, DASHBOARD_TARGET_YEAR, "ratio"),
            fetchElderlyTop5(DASHBOARD_BASE_YEAR, DASHBOARD_TARGET_YEAR, "absolute"),
            fetchElderlyTrend(2017, 2050),
        ]);

        renderTopTablesFromApis(ratioTop5, absoluteTop5);
        renderSummaryFromTrendAndTop(trendItems, ratioTop5);

        await trendPromise;
    } catch (err) {
        console.error("대시보드 초기화 실패:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
  // 구 체크박스 생성
  initRegionCheckboxes();

  // 기존 대시보드 초기화 로직
  initDashboard();

  const forecastBtn = document.getElementById("btn-load-forecast");
  if (forecastBtn) {
    forecastBtn.addEventListener("click", handleForecastClick);
  }
});
