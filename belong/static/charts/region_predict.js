// =====================
// 1) 히스토리 조회 API
// =====================
async function fetchHistory(region) {
    const start = 2017;
    const end = 2023;   // 백엔드 기준

    const url = `/api/elderly-stats/${region}/${start}/${end}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("히스토리 조회 실패");

    return await res.json();
}


// =====================
// 2) 예측 API
// =====================
async function fetchPrediction(region, year) {
    const url = `/api/predictions/${region}/${year}`;

    const res = await fetch(url, { method: "POST" });
    if (!res.ok) throw new Error("예측 요청 실패");

    const json = await res.json();
    return json.result;
}


// =====================
// 3) 메인 로직
// =====================
async function loadRegionForecast(region, year) {
    showLoading();

    try {
        const history = await fetchHistory(region);
        const prediction = await fetchPrediction(region, year);

        hideLoading();
        renderSummary(history, prediction, year);
        renderChart(history, prediction);
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
// 4) Summary 카드 채우기
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
// 5) Chart.js
// =====================
let chartInstance = null;

function renderChart(history, prediction) {
    const ctx = document.getElementById("forecast-chart");

    const labels = history.map(d => d.year).concat(prediction.year);
    const historyData = history.map(d => d.elderly_population);
    const forecastData = [ ...Array(history.length).fill(null), prediction.prediction ];

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "과거 데이터",
                    data: historyData,
                    borderColor: "#007bff",
                    borderWidth: 2
                },
                {
                    label: `예측 (${prediction.year})`,
                    data: forecastData,
                    borderColor: "#ff5733",
                    borderDash: [5,5],
                    borderWidth: 2
                }
            ]
        }
    });
}


// =====================
// 6) UI Helpers
// =====================
function showLoading() {
    document.getElementById("loading").style.display = "block";
}
function hideLoading() {
    document.getElementById("loading").style.display = "none";
}
function showError(msg) {
    const e = document.getElementById("error-message");
    e.innerText = msg;
    e.style.display = "block";
}
