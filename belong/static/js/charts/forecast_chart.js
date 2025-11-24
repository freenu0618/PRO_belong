let chart = null;

document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById('forecastChart');

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: "예측 위험도",
                data: [],
                borderWidth: 2,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,0.3)"
            }]
        },
        options: {
            responsive: true,
            tension: 0.3
        }
    });

    // 페이지 처음 로딩 시 기본 데이터 Fetch
//    fetchPrediction("강남구");
});
const REGION_MAP = {
    "강남구": "gangnam",
    "종로구": "jongno",
    "동작구": "dongjak"
    };

async function fetchPrediction(region) {
    showLoading(true);

    try {
        // MOCK 데이터 사용 (백엔드 완성 후 변경)
        const filename = `/static/mock/forecast_${REGION_MAP[region]}.json`;
        const response = await fetch(filename);
        const json = await response.json();


        const history = json.data.history;

        const labels = history.map(h => h.year);
        const values = history.map(h => h.value);

        updateChart(labels, values);

    } catch (error) {
        console.error("데이터 요청 실패:", error);
    } finally {
        showLoading(false);
    }
}


function updateChart(labels, dataset) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = dataset;
    chart.update();
}

function showLoading(state) {
    const loader = document.getElementById("loading");
    if (loader) loader.style.display = state ? "block" : "none";
}
