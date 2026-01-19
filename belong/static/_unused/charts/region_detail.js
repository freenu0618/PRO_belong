// static/charts/region_detail.js
// 지역 상세(하나의 구 깊게 보기) 페이지 전용 JS
// - 연도 범위 선택(from/to) + 갱신
// - 노인 인구/고독사: 실측(history) + 예측(forecast) 타임라인
// - 리스크 레이더(증가율/최근3년 평균)
// - URL 상태 동기화: ?from=2017&to=2023

let timelineChart = null;
let radarChart = null;

const REGION_MIN_YEAR = 2017;
const REGION_MAX_YEAR = 2035;

function clampYear(y) {
  if (!Number.isFinite(y)) return REGION_MIN_YEAR;
  return Math.min(REGION_MAX_YEAR, Math.max(REGION_MIN_YEAR, y));
}

function readRegionStateFromUrl() {
  const qs = new URLSearchParams(location.search);
  const from = parseInt(qs.get("from"), 10);
  const to = parseInt(qs.get("to"), 10);
  return {
    from: Number.isNaN(from) ? null : clampYear(from),
    to: Number.isNaN(to) ? null : clampYear(to),
  };
}

function writeRegionStateToUrl(from, to) {
  const qs = new URLSearchParams(location.search);
  qs.set("from", String(from));
  qs.set("to", String(to));
  history.replaceState(null, "", `${location.pathname}?${qs.toString()}`);
}

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return await res.json();
}

/**
 * API 응답을 안전하게 data로 정리
 * - 기대 형태: {status:'success', data:{history:[], forecast:[]}}
 * - 혹시 {items:[]} 같은 형태면 items를 history로 처리
 */
function normalizeForecastPayload(payload) {
  if (!payload) return { history: [], forecast: [], region: "" };

  // {status, data}
  if (payload.data && typeof payload.data === "object") {
    return {
      region: payload.data.region || payload.region || "",
      history: Array.isArray(payload.data.history) ? payload.data.history : [],
      forecast: Array.isArray(payload.data.forecast) ? payload.data.forecast : [],
    };
  }

  // {items:[]}
  if (Array.isArray(payload.items)) {
    return {
      region: payload.region || "",
      history: payload.items,
      forecast: [],
    };
  }

  return { history: [], forecast: [], region: "" };
}

/**
 * row에서 값 추출(데이터 구조가 조금 달라도 최대한 살려서 렌더)
 */
function extractValue(row) {
  if (!row || typeof row !== "object") return null;

  const candidates = [
    "value",
    "elderly_population",
    "population",
    "count",
    "lonely_death",
    "lonely_deaths",
    "lonely_count",
    "death_count",
    "deaths",
    "predicted_value",
    "y",
  ];

  for (const k of candidates) {
    if (row[k] === 0) return 0;
    if (row[k] != null && row[k] !== "") {
      const n = Number(row[k]);
      if (Number.isFinite(n)) return n;
    }
  }
  return null;
}

function extractYear(row) {
  const y = Number(row?.year);
  return Number.isFinite(y) ? y : null;
}

function initYearSelects() {
  const startSel = document.getElementById("region-year-start");
  const endSel = document.getElementById("region-year-end");
  if (!startSel || !endSel) return;

  // 옵션 초기화
  startSel.innerHTML = "";
  endSel.innerHTML = "";

  for (let y = REGION_MIN_YEAR; y <= REGION_MAX_YEAR; y++) {
    const opt1 = document.createElement("option");
    opt1.value = String(y);
    opt1.textContent = `${y}년`;
    startSel.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = String(y);
    opt2.textContent = `${y}년`;
    endSel.appendChild(opt2);
  }

  // URL 있으면 우선 반영, 없으면 기본값
  const { from, to } = readRegionStateFromUrl();
  const defaultFrom = from ?? 2017;
  const defaultTo = to ?? 2028;

  startSel.value = String(defaultFrom);
  endSel.value = String(defaultTo);
}

function bindEvents(region) {
  const btn = document.getElementById("region-refresh-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const old = btn.textContent;
    btn.disabled = true;
    btn.textContent = "불러오는 중...";

    try {
      await loadRegionData(region);
    } catch (err) {
      console.error(err);
      alert("데이터를 다시 불러오지 못했습니다.");
    } finally {
      btn.disabled = false;
      btn.textContent = old || "갱신";
    }
  });
}

function setHeaderSubtitle(region, startYear, endYear) {
  const el = document.getElementById("region-subtitle");
  if (!el) return;
  el.textContent = `${region} · ${startYear}~${endYear}`;
}

async function loadRegionData(region) {
  const startSel = document.getElementById("region-year-start");
  const endSel = document.getElementById("region-year-end");
  if (!startSel || !endSel) return;

  let startYear = clampYear(parseInt(startSel.value, 10));
  let endYear = clampYear(parseInt(endSel.value, 10));

  // 범위 보정
  if (startYear > endYear) {
    const tmp = startYear;
    startYear = endYear;
    endYear = tmp;
    startSel.value = String(startYear);
    endSel.value = String(endYear);
  }

  writeRegionStateToUrl(startYear, endYear);
  setHeaderSubtitle(region, startYear, endYear);

  // API 호출 (둘 다 성공해야 타임라인/레이더가 의미 있음)
  const [elderlyRaw, lonelyRaw] = await Promise.all([
    fetchJson(`/api/elderly/forecast/${encodeURIComponent(region)}`),
    fetchJson(`/api/lonely/forecast?region=${encodeURIComponent(region)}`),
  ]);

  const elderlyData = normalizeForecastPayload(elderlyRaw);
  const lonelyData = normalizeForecastPayload(lonelyRaw);

  renderTimelineChart(region, elderlyData, lonelyData, startYear, endYear);
  renderRadarChart(region, elderlyData, lonelyData, startYear, endYear);
  updateRiskCards(region, elderlyData, lonelyData, startYear, endYear);
}

function renderTimelineChart(region, elderlyData, lonelyData, startYear, endYear) {
  const canvas = document.getElementById("timelineChart");
  if (!canvas) return;

  if (typeof Chart === "undefined") {
    console.error("[region_detail] Chart.js가 로드되지 않았습니다.");
    return;
  }

  // 필터링 + 정렬
  const eHistory = (elderlyData.history || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((r) => r.year != null && r.year >= startYear && r.year <= endYear)
    .sort((a, b) => a.year - b.year);

  const eForecast = (elderlyData.forecast || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((r) => r.year != null && r.year >= startYear && r.year <= endYear)
    .sort((a, b) => a.year - b.year);

  const lHistory = (lonelyData.history || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((r) => r.year != null && r.year >= startYear && r.year <= endYear)
    .sort((a, b) => a.year - b.year);

  const lForecast = (lonelyData.forecast || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((r) => r.year != null && r.year >= startYear && r.year <= endYear)
    .sort((a, b) => a.year - b.year);

  const allYears = Array.from(
    new Set([
      ...eHistory.map((r) => r.year),
      ...eForecast.map((r) => r.year),
      ...lHistory.map((r) => r.year),
      ...lForecast.map((r) => r.year),
    ])
  ).sort((a, b) => a - b);

  // 값 매핑(해당 연도 데이터 없으면 null)
  const elderlyHistoryValues = allYears.map(
    (y) => eHistory.find((r) => r.year === y)?._v ?? null
  );
  const elderlyForecastValues = allYears.map(
    (y) => eForecast.find((r) => r.year === y)?._v ?? null
  );

  const lonelyHistoryValues = allYears.map(
    (y) => lHistory.find((r) => r.year === y)?._v ?? null
  );
  const lonelyForecastValues = allYears.map(
    (y) => lForecast.find((r) => r.year === y)?._v ?? null
  );

  if (timelineChart) timelineChart.destroy();

  const ctx = canvas.getContext("2d");
  timelineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: allYears,
      datasets: [
        {
          label: "노인 인구 (실측)",
          data: elderlyHistoryValues,
          borderColor: "#2563EB",
          backgroundColor: "rgba(37, 99, 235, 0.12)",
          tension: 0.25,
          spanGaps: true,
        },
        {
          label: "노인 인구 (예측)",
          data: elderlyForecastValues,
          borderColor: "#60A5FA",
          backgroundColor: "rgba(96, 165, 250, 0.10)",
          borderDash: [6, 6],
          tension: 0.25,
          spanGaps: true,
        },
        {
          label: "고독사 (실측)",
          data: lonelyHistoryValues,
          borderColor: "#E11D48",
          backgroundColor: "rgba(225, 29, 72, 0.12)",
          tension: 0.25,
          spanGaps: true,
        },
        {
          label: "고독사 (예측)",
          data: lonelyForecastValues,
          borderColor: "#FB7185",
          backgroundColor: "rgba(251, 113, 133, 0.10)",
          borderDash: [6, 6],
          tension: 0.25,
          spanGaps: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: `${region} · 시간 흐름(실측/예측)`,
        },
        legend: { display: true },
        tooltip: { mode: "index", intersect: false },
      },
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          ticks: { autoSkip: true, maxTicksLimit: 10 },
        },
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

function renderRadarChart(region, elderlyData, lonelyData, startYear, endYear) {
  const canvas = document.getElementById("riskRadarChart");
  if (!canvas) return;

  if (typeof Chart === "undefined") {
    console.error("[region_detail] Chart.js가 로드되지 않았습니다.");
    return;
  }

  const eHistory = (elderlyData.history || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((row) => row.year != null && row.year >= startYear && row.year <= endYear)
    .sort((a, b) => a.year - b.year);

  const lHistory = (lonelyData.history || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((row) => row.year != null && row.year >= startYear && row.year <= endYear)
    .sort((a, b) => a.year - b.year);

  // 계산이 가능한 최소 조건
  if (eHistory.length < 2 || lHistory.length < 2) {
    if (radarChart) radarChart.destroy();
    return;
  }

  const firstE = eHistory[0];
  const lastE = eHistory[eHistory.length - 1];
  const firstL = lHistory[0];
  const lastL = lHistory[lHistory.length - 1];

  const eFirstVal = firstE._v ?? 0;
  const eLastVal = lastE._v ?? 0;
  const lFirstVal = firstL._v ?? 0;
  const lLastVal = lastL._v ?? 0;

  const elderlyGrowthRate = eFirstVal > 0 ? ((eLastVal - eFirstVal) / eFirstVal) * 100 : 0;
  const lonelyGrowthRate = lFirstVal > 0 ? ((lLastVal - lFirstVal) / lFirstVal) * 100 : 0;

  // 최근 3년 평균 고독사(가능하면 마지막 3개 사용)
  const last3Lonely = lHistory.slice(-3);
  const avgLonelyLast3 =
    last3Lonely.reduce((sum, r) => sum + (r._v ?? 0), 0) / (last3Lonely.length || 1);

  const labels = ["노인 인구 증가율(%)", "고독사 증가율(%)", "최근 3년 평균 고독사"];
  const dataValues = [elderlyGrowthRate, lonelyGrowthRate, avgLonelyLast3];

  if (radarChart) radarChart.destroy();

  const ctx = canvas.getContext("2d");
  radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: `${region} 리스크 프로파일`,
          data: dataValues,
          borderColor: "#7C3AED",
          backgroundColor: "rgba(124, 58, 237, 0.18)",
          pointBackgroundColor: "#7C3AED",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        title: { display: true, text: "리스크 요약(증가율/최근 평균)" },
      },
      scales: {
        r: {
          beginAtZero: true,
          ticks: { display: true },
        },
      },
    },
  });
}

function updateRiskCards(region, elderlyData, lonelyData, startYear, endYear) {
  // 카드 요소(없어도 에러 안 나게)
  const riskEl = document.getElementById("risk-level");
  const riskDescEl = document.getElementById("risk-desc");
  const elderlyEl = document.getElementById("elderly-trend-text");
  const lonelyEl = document.getElementById("lonely-trend-text");

  const lHistory = (lonelyData.history || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((row) => row.year != null && row.year >= startYear && row.year <= endYear)
    .sort((a, b) => a.year - b.year);

  const eHistory = (elderlyData.history || [])
    .map((r) => ({ ...r, year: extractYear(r), _v: extractValue(r) }))
    .filter((row) => row.year != null && row.year >= startYear && row.year <= endYear)
    .sort((a, b) => a.year - b.year);

  let riskLevel = "정보 부족";
  let riskDescription = "선택한 기간의 데이터가 충분하지 않습니다.";
  let elderlyText = "데이터 부족";
  let lonelyText = "데이터 부족";

  // 노인 인구 추세(간단)
  if (eHistory.length >= 2) {
    const a = eHistory[0]._v ?? 0;
    const b = eHistory[eHistory.length - 1]._v ?? 0;
    const diff = b - a;
    if (diff > 0) elderlyText = "증가 추세";
    else if (diff < 0) elderlyText = "감소 추세";
    else elderlyText = "정체";
  }

  // 고독사 리스크(증가율 기반 간단 판정)
  if (lHistory.length >= 2) {
    const a = lHistory[0]._v ?? 0;
    const b = lHistory[lHistory.length - 1]._v ?? 0;

    const rate = a > 0 ? ((b - a) / a) * 100 : (b > 0 ? 999 : 0);

    if (rate <= 0) {
      riskLevel = "보통";
      riskDescription = "발생 건수는 있으나 증가 추세는 뚜렷하지 않습니다.";
      lonelyText = "큰 변화 없는 수준";
    } else if (rate > 0 && rate <= 30) {
      riskLevel = "주의";
      riskDescription = "고독사 발생이 서서히 증가하고 있어 모니터링이 필요합니다.";
      lonelyText = "완만한 증가 추세";
    } else {
      riskLevel = "경계";
      riskDescription = "고독사 발생이 빠르게 증가하고 있어 집중적인 관리가 필요합니다.";
      lonelyText = "급격한 증가 추세";
    }
  }

  if (riskEl) riskEl.textContent = riskLevel;
  if (riskDescEl) riskDescEl.textContent = riskDescription;
  if (elderlyEl) elderlyEl.textContent = elderlyText;
  if (lonelyEl) lonelyEl.textContent = lonelyText;
}

// 페이지 진입 시 호출되는 함수 (region_detail.html에서 initRegionDetailPage("강남구") 형태로 호출)
function initRegionDetailPage(regionName) {
  const region = (regionName || "").trim();
  if (!region) return;

  initYearSelects();
  bindEvents(region);

  // 초기 로딩
  loadRegionData(region).catch((err) => {
    console.error(err);
    alert("초기 데이터를 불러오지 못했습니다.");
  });
}

/* 전역에서 쓸 수 있게 */
window.initRegionDetailPage = initRegionDetailPage;
