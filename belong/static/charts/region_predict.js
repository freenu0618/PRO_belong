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
// 2) 예측 API
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
// 3) 메인 로직
// =====================
async function loadRegionForecast(region, year) {
    showLoading();

    try {
        const history = await fetchHistory(region);
        const prediction = await fetchPrediction(region, year);

        if (!Array.isArray(history) || history.length === 0) {
            throw new Error("히스토리 데이터 없음");
        }

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

    // 연도 라벨: 과거(2017~2023) + 예측연도(예: 2029)
    const labels = history.map(d => d.year).concat(prediction.year);

    // 과거 데이터 (파란선)
    const historyData = history.map(d => d.elderly_population);

    // 예측선 데이터
    // 앞부분은 null, 2023 위치에는 마지막 값, 2029에는 예측값
    const lastIndex = history.length - 1;
    const forecastData = history.map((d, i) =>
        i === lastIndex ? d.elderly_population : null
    ).concat(prediction.prediction);

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
                pointRadius: 5,
                fill: false
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,      // 모달 안에서 가득 차게
        scales: {
            x: {
                offset: false            // ✅ 양끝 여백 없애기 (요게 핵심)
            }
        }
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
