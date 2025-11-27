// =====================
// 글로벌 상태 & Chart 인스턴스
// =====================
let currentRegion = null;
let currentYear = null;

let mainChartInstance = null;       // 실측 + 선택 예측 차트
let historyChartInstance = null;    // 예측 이력 차트


// =====================
// 1) 히스토리 조회 API
// =====================
async function fetchHistory(region) {
    const start = 2017;
    const end = 2023;   // 백엔드 기준

    const url = `/api/elderly-stats/${encodeURIComponent(region)}/${start}/${end}`;

    const res = await fetch(url);
    if (!res.ok) {
        throw new Error("히스토리 조회 실패 (HTTP " + res.status + ")");
    }

    // 이 엔드포인트는 리스트 자체를 반환함: [ {year, elderly_population}, ... ]
    const json = await res.json();

    if (!Array.isArray(json) || json.length === 0) {
        throw new Error("히스토리 데이터 형식 오류 또는 비어 있음");
    }

    return json;
}


// =====================
// 2) 예측 API (POST)
// =====================
async function fetchPrediction(region, year) {
    const url = `/api/predictions/${encodeURIComponent(region)}/${year}`;

    const res = await fetch(url, { method: "POST" });
    if (!res.ok) {
        throw new Error("예측 요청 실패 (HTTP " + res.status + ")");
    }

    // POST /predictions 는 { saved: true, result: {...} } 형태
    const json = await res.json();

    if (!json || !json.result) {
        throw new Error("예측 데이터 형식 오류");
    }

    return json.result;  // { year, prediction, ... }
}


// =====================
// 3) 예측 이력 조회 API
// =====================
async function fetchPredictionHistory(region) {
    const url = `/api/predictions/history/${encodeURIComponent(region)}`;

    const res = await fetch(url);
    if (!res.ok) {
        // 이력 없다고 해서 전체 화면을 죽일 필요는 없음
        console.warn("예측 이력 조회 실패 (HTTP " + res.status + ")");
        return [];
    }

    const json = await res.json();
    if (!Array.isArray(json)) {
        console.warn("예측 이력 데이터 형식이 배열이 아님");
        return [];
    }
    return json;   // [{ region, year, prediction, ... }, ...]
}


// =====================
// 4) 메인 로직
// =====================
async function loadRegionForecast(region, year) {
    currentRegion = region;
    currentYear = year;

    showLoading();
    hideError();

    try {
        const [history, prediction, historyList] = await Promise.all([
            fetchHistory(region),
            fetchPrediction(region, year),
            fetchPredictionHistory(region),
        ]);

        if (!Array.isArray(history) || history.length === 0) {
            throw new Error("히스토리 데이터 없음");
        }

        hideLoading();
        renderSummary(history, prediction, year);
        renderMainChart(history, prediction);
        renderHistoryChart(historyList);

        document.getElementById("chart-btn-section").style.display = "block";

        // 자동 스크롤 다운
        setTimeout(() => {
            window.scrollTo({ top: 400, behavior: "smooth" });
        }, 500);

    } catch (err) {
        console.error(err);
        hideLoading();
        showError("데이터를 불러오지 못했습니다. 입력값을 확인해주세요.");
    }
}


// =====================
// 5) Summary 카드 채우기
// =====================
function renderSummary(history, prediction, year) {

    const latest = history[history.length - 1].elderly_population;
    const predicted = prediction.prediction;

    const growth = (((predicted - latest) / latest) * 100).toFixed(1);

    document.getElementById("latest-pop").innerText = latest.toLocaleString();
    document.getElementById("predicted-pop").innerText = predicted.toLocaleString();
    document.getElementById("growth-rate").innerText = growth + "%";

    document.getElementById("summary-section").style.display = "block";
}


// =====================
// 6) 메인 Chart.js (실측 + 선택 예측)
// =====================
function renderMainChart(history, prediction) {
    const ctx = document.getElementById("forecast-chart");
    if (!ctx) return;

    // 연도 라벨: 과거(2017~2023) + 예측연도(예: 2029)
    const labels = history.map(d => d.year).concat(prediction.year);

    // 과거 데이터 (파란선)
    const historyData = history.map(d => d.elderly_population);

    // 실측 마지막 지점부터 예측 연도까지 이어지는 선
    const lastIndex = history.length - 1;
    const forecastData = history.map((d, i) =>
        i === lastIndex ? d.elderly_population : null
    ).concat(prediction.prediction);

    if (mainChartInstance) mainChartInstance.destroy();

    mainChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "과거 데이터",
                    data: historyData,
                    borderColor: "#007bff",
                    borderWidth: 2,
                    pointRadius: 4,
                    fill: false
                },
                {
                    label: `예측 (${prediction.year})`,
                    data: forecastData,
                    borderColor: "#ff5733",
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: (context) => {
                        const index = context.dataIndex;
                        const total = context.chart.data.labels.length;
                        // 마지막 예측 포인트만 크게
                        return index === total - 1 ? 6 : (forecastData[index] ? 4 : 0);
                    },
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,      // 모달 안에서 가득 차게
            scales: {
                x: {
                    offset: false,           // 양끝 여백 제거
                    title: {
                        display: true,
                        text: "연도"
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: "독거노인 인구 수"
                    },
                    ticks: {
                        callback: (value) => value.toLocaleString("ko-KR")
                    }
                }
            }
        }
    });
}


// =====================
// 7) 예측 이력 Chart.js
// =====================
function renderHistoryChart(historyList) {
    const section = document.getElementById("history-section");
    const canvas = document.getElementById("prediction-history-chart");
    if (!section || !canvas) return;

    if (!historyList || historyList.length === 0) {
        section.style.display = "none";
        return;
    }

    const sorted = [...historyList].sort((a, b) => a.year - b.year);
    const labels = sorted.map(r => r.year);
    const data = sorted.map(r => r.prediction);
    const lastIndex = labels.length - 1;

    if (historyChartInstance) historyChartInstance.destroy();

    historyChartInstance = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "예측 이력",
                    data,
                    borderColor: "#28a745",
                    borderWidth: 2,
                    tension: 0.25,
                    pointRadius: (ctx) => ctx.dataIndex === lastIndex ? 6 : 4,
                    pointBackgroundColor: (ctx) =>
                        ctx.dataIndex === lastIndex ? "#dc3545" : "#28a745",
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "연도"
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: "예측 독거노인 인구 수"
                    },
                    ticks: {
                        callback: (value) => value.toLocaleString("ko-KR")
                    }
                }
            }
        }
    });

    section.style.display = "block";
}


// =====================
// 8) UI Helpers
// =====================
function showLoading() {
    const el = document.getElementById("loading");
    if (el) el.style.display = "block";
}
function hideLoading() {
    const el = document.getElementById("loading");
    if (el) el.style.display = "none";
}
function showError(msg) {
    const e = document.getElementById("error-message");
    if (!e) return;
    e.innerText = msg;
    e.style.display = "block";
}
function hideError() {
    const e = document.getElementById("error-message");
    if (!e) return;
    e.innerText = "";
    e.style.display = "none";
}


// =====================
// 9) 페이지 초기화 함수
// =====================
function initRegionDetail(region, year) {
    currentRegion = region;
    currentYear = year;

    const form = document.getElementById("predict-form");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const yearInput = document.getElementById("predict-year");
            if (!yearInput) return;

            const newYear = yearInput.value.trim();
            if (!newYear) return;

            await loadRegionForecast(region, newYear);
        });
    }

    loadRegionForecast(region, year);
}
