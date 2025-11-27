// ✅ 1) API → 실패 시 mock fallback
async function fetchForecast(region) {
    const apiUrl = `/api/predict?region=${region}`;
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

let elderlyTrendChart = null;

async function renderElderlyTrendChart() {
  const items = await fetchElderlyTrend(2017, 2050);

  if (!items.length) return;

  const labels = items.map(d => d.year);

  // 실제값/예측값을 두 개 데이터셋으로 분리 (null로 끊어서 표시)
  const actualData = items.map(d => d.is_forecast ? null : d.total_elderly_population);
  const forecastData = items.map(d => d.is_forecast ? d.total_elderly_population : null);

  const ctx = document.getElementById("elderlyTrendChart").getContext("2d");

  // 이전 차트가 있으면 파괴
  if (elderlyTrendChart) {
    elderlyTrendChart.destroy();
  }

  elderlyTrendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "독거노인 인구(실측)",
          data: actualData,
          borderColor: "#4e73df",
          backgroundColor: "rgba(78, 115, 223, 0.05)",
          spanGaps: false,
        },
        {
          label: "독거노인 인구(예측)",
          data: forecastData,
          borderColor: "#e74a3b",
          backgroundColor: "rgba(231, 74, 59, 0.05)",
          borderDash: [5, 5],
          spanGaps: false,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v = ctx.parsed.y;
              if (v == null) return "";
              return ctx.dataset.label + ": " + v.toLocaleString() + "명";
            },
          },
        },
      },
      scales: {
        y: {
          ticks: {
            callback: (v) => v.toLocaleString() + "명",
          },
        },
      },
    },
  });
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
