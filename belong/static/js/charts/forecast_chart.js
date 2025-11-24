// ✅ 1) API → 실패 시 mock fallback
async function fetchForecast(region) {
    const apiUrl = `/api/v1/predict?region=${region}`;
    const mockUrl = `/static/mock/forecast_${region}.json`;

    try {
        const response = await fetch(apiUrl);

        if (!response.ok) {
            console.warn(`API returned ${response.status}, switching to mock...`);
            return await fetchMock(mockUrl);
        }

        const json = await response.json();

        if (!json?.data || !json.data.forecast) {
            console.warn(`API responded but no forecast available, using mock`);
            return await fetchMock(mockUrl);
        }

        return json.data;
    } catch (err) {
        console.error("API request failed, switching to mock:", err);
        return await fetchMock(mockUrl);
    }
}

// Helper fn
async function fetchMock(url) {
    const res = await fetch(url);
    return res.json();
}


// ✅ 2) Update Chart with new data
async function updateForecastChart(region) {
    showLoading();

    const data = await fetchForecast(region);

    hideLoading();

    updateChart(
        data.history.map(d => d.year),
        [
            {
                label: "과거 데이터",
                data: data.history.map(d => d.value)
            },
            {
                label: "예측 데이터",
                data: data.forecast ? data.forecast.map(d => d.value) : [],
                dashed: true
            }
        ]
    );
}
function showError(msg) {
    document.getElementById("error-message").innerText = msg;
    document.getElementById("error-message").style.display = "block";
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
