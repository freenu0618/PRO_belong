// =============================
// 1) API → mock fallback
// =============================
async function fetchForecast(region) {
    const apiUrl = `/api/predict?region=${region}`;
    const mockUrl = `/static/mock/forecast_${region}.json`;

    try {
        const response = await fetch(apiUrl);

        if (!response.ok) {
            console.warn("API 실패 → mock 사용");
            return await fetchMock(mockUrl);
        }

        const json = await response.json();

        if (!json?.data?.history) {
            console.warn("API 데이터 없음 → mock 사용");
            return await fetchMock(mockUrl);
        }

        return json.data;
    } catch (err) {
        console.error("API 오류:", err);
        return await fetchMock(mockUrl);
    }
}

async function fetchMock(url) {
    const res = await fetch(url);
    return await res.json();
}


// =============================
// 2) 차트 업데이트
// =============================
let chartInstance = null;

function updateChart(labels, datasets) {
    const ctx = document.getElementById("forecast-chart").getContext("2d");

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: datasets.map(ds => ({
                label: ds.label,
                data: ds.data,
                borderWidth: 2,
                borderColor: ds.dashed ? "#ff9800" : "#2196f3",
                borderDash: ds.dashed ? [5, 5] : [],
                fill: false
            }))
        },
        options: {
            responsive: true
        }
    });
}


// =============================
// 3) 페이지 렌더링
// =============================
async function updateForecastChart(region) {
    showLoading();

    const data = await fetchForecast(region);

    hideLoading();

    if (!data.history) {
        showError("예측 데이터를 찾을 수 없습니다.");
        return;
    }

    hideError();

    // Summary 계산
    const latest = data.history[data.history.length - 1]?.value ?? "-";
    const forecastLast = data.forecast?.[data.forecast.length - 1]?.value ?? "-";

    document.getElementById("latest-value").innerText = latest.toLocaleString();
    document.getElementById("growth-rate").innerText =
        (calcGrowth(data.history) + "%") ?? "-";
    document.getElementById("forecast-summary").innerText =
        forecastLast.toLocaleString();

    document.getElementById("summary-section").style.display = "flex";
    document.getElementById("chart-section").style.display = "block";

    // 차트 생성
    const labels = [
        ...data.history.map(d => d.year),
        ...data.forecast.map(d => d.year)
    ];

    const historyYears = data.history.map(d => d.year).length;

    updateChart(
        labels,
        [
            {
                label: "과거 데이터",
                data: data.history.map(d => d.value)
            },
            {
                label: "예측 데이터",
                data: [
                    ...Array(historyYears).fill(null),
                    ...data.forecast.map(d => d.value)
                ],
                dashed: true
            }
        ]
    );
}

// =============================
// 4) 유틸
// =============================
function calcGrowth(arr) {
    if (!arr || arr.length < 2) return "-";
    const first = arr[0].value;
    const last = arr[arr.length - 1].value;
    return (((last - first) / first) * 100).toFixed(1);
}

function showError(msg) {
    const el = document.getElementById("error-message");
    el.innerText = msg;
    el.style.display = "block";
}

function hideError() {
    document.getElementById("error-message").style.display = "none";
}

function showLoading() {
    document.getElementById("loading").style.display = "block";
}

function hideLoading() {
    document.getElementById("loading").style.display = "none";
}
