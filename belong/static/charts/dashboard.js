// =========================
// 0. 공통 헬퍼
// =========================
let dashboardChart = null;
let forecastChart = null;

async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
    }
    return await res.json();
}

// =========================
// 1) /api/elderly/population 불러오기
// =========================
async function fetchDashboard() {
    const json = await fetchJson("/api/elderly/population");

    // 백엔드 포맷 1) { status, data: [...] } 혹은 2) [ ... ]
    const data = Array.isArray(json) ? json : json.data;
    if (!data || !Array.isArray(data)) {
        throw new Error("대시보드 데이터 형식 오류");
    }
    return data;
}

// =========================
// 2) Summary 카드 렌더링
// =========================
function renderSummary(data) {
    if (!data.length) return;

    const totalEl = document.getElementById("summary-total");
    const topEl = document.getElementById("summary-growth-top");
    const bottomEl = document.getElementById("summary-growth-bottom");

    const total = data.reduce(
        (sum, r) => sum + (r.latest_value || 0),
        0
    );

    const sortedByGrowth = [...data].sort(
        (a, b) => (b.growth_rate || 0) - (a.growth_rate || 0)
    );
    const top = sortedByGrowth[0];
    const bottom = sortedByGrowth[sortedByGrowth.length - 1];

    if (totalEl) totalEl.textContent = total.toLocaleString("ko-KR");
    if (topEl && top) topEl.textContent = top.region;
    if (bottomEl && bottom) bottomEl.textContent = bottom.region;
}

// =========================
// 3) TOP5 테이블 렌더링
//      - 왼쪽: 증가율 TOP5
//      - 오른쪽: 인구수 TOP5
// =========================
function renderTopTables(data) {
    const growthBody = document.getElementById("population-growth-body");
    const countBody = document.getElementById("population-count-body");
    if (!growthBody || !countBody) return;

    growthBody.innerHTML = "";
    countBody.innerHTML = "";

    const sortedByGrowth = [...data].sort(
        (a, b) => (b.growth_rate || 0) - (a.growth_rate || 0)
    );
    const sortedByCount = [...data].sort(
        (a, b) => (b.latest_value || 0) - (a.latest_value || 0)
    );

    const topGrowth = sortedByGrowth.slice(0, 5);
    const topCount = sortedByCount.slice(0, 5);

    topGrowth.forEach(row => {
        const latest = row.latest_value || 0;
        const rate = (row.growth_rate || 0) * 100;
        growthBody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${latest.toLocaleString("ko-KR")}</td>
                <td>${rate.toFixed(2)}%</td>
            </tr>
        `;
    });

    topCount.forEach(row => {
        const latest = row.latest_value || 0;
        const rate = (row.growth_rate || 0) * 100;
        countBody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${latest.toLocaleString("ko-KR")}</td>
                <td>${rate.toFixed(2)}%</td>
            </tr>
        `;
    });
}

// =========================
// 4) Chart.js 라인 차트 렌더링
// =========================
function renderChart(data) {
    const canvas = document.getElementById("dashboard-chart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const first = data[0];
    if (!first) {
        console.warn("차트용 데이터가 비어 있습니다.");
        return;
    }

    // values / value / history 중 하나를 사용
    const seriesForFirst =
        (Array.isArray(first.values) && first.values) ||
        (Array.isArray(first.value) && first.value) ||
        (Array.isArray(first.history) && first.history);

    if (!seriesForFirst) {
        console.warn("차트 데이터 형식이 올바르지 않습니다. (values/value/history 없음)");
        return;
    }

    const years = seriesForFirst.map(v => v.year);

    const datasets = data.map(regionRow => {
        const series =
            (Array.isArray(regionRow.values) && regionRow.values) ||
            (Array.isArray(regionRow.value) && regionRow.value) ||
            (Array.isArray(regionRow.history) && regionRow.history) ||
            [];
        return {
            label: regionRow.region,
            data: series.map(v => v.value),
            borderWidth: 2,
            tension: 0.25
        };
    });

    if (dashboardChart) {
        dashboardChart.destroy();
    }

    dashboardChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: years,
            datasets
        },
        options: {
            responsive: true,
            interaction: {
                mode: "nearest",
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: "bottom"
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || "";
                            const value = context.parsed.y;
                            return `${label}: ${value.toLocaleString("ko-KR")}`;
                        }
                    }
                }
            },
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
                        text: "노인 인구 수"
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// =========================
// 5) Forecast(예측) 섹션
// =========================
// 🔹 예측 버튼 클릭 핸들러
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

    // 1) 네트워크 / JSON 파싱만 try-catch로 감싸기
    let res;
    try {
        res = await fetch(url);
    } catch (err) {
        console.error("[Forecast] fetch 실패:", err);
        alert("예측 데이터를 불러오지 못했습니다. 네트워크 상태를 확인해 주세요.");
        return;
    }

    let json = null;
    try {
        json = await res.json();
    } catch (err) {
        console.error("[Forecast] JSON 파싱 실패:", err);
        alert("예측 데이터를 불러오지 못했습니다. 서버 응답 형식을 확인해 주세요.");
        return;
    }

    console.log("[Forecast] 응답:", res.status, json);

    // 2) 백엔드 에러 처리
    if (!res.ok) {
        const msg =
            (json && json.message) ||
            `예측 API 호출 실패 (HTTP ${res.status})`;
        openForecastModal(region, {
            message: msg,
            history: [],
            forecast: []
        });
        return;
    }

    if (json.status && json.status.toLowerCase() === "error") {
        const msg =
            json.message || "예측 데이터를 찾을 수 없습니다.";
        openForecastModal(region, {
            message: msg,
            history: [],
            forecast: []
        });
        return;
    }

    // 3) 정상 데이터 → 모달 + 차트 렌더링
    const payload = json.data || json;
    try {
        openForecastModal(region, payload);
    } catch (err) {
        // 여기에서 나는 에러는 네트워크 문제가 아니라 프론트쪽 버그
        console.error("[Forecast] 모달 렌더링 실패:", err);
        alert("예측 결과를 화면에 표시하는 중 오류가 발생했습니다. 콘솔 로그를 확인해 주세요.");
    }
}

function openForecastModal(region, data) {
    const modalEl = document.getElementById("forecastModal");
    const titleEl = document.getElementById("forecastModalLabel");
    const msgEl = document.getElementById("forecast-modal-message");
    const tbody = document.getElementById("forecast-modal-body");

    // 모달 구조가 없는 경우: 간단 alert로 대체
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

    // 🔹 차트 렌더링 (여기서 에러가 나면 catch에서 잡히도록 try 내부에서 호출 X)
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

let forecastChart = null;

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
                    tension: 0.2
                },
                {
                    label: "예측",
                    data: forecastSeries,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: "nearest",
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: "bottom"
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || "";
                            const value = context.parsed.y;
                            if (value == null) return "";
                            return `${label}: ${value.toLocaleString("ko-KR")}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: "연도" }
                },
                y: {
                    title: { display: true, text: "노인 인구 수" },
                    beginAtZero: true
                }
            }
        }
    });
}


// =========================
// 6) 초기화
// =========================
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const data = await fetchDashboard();
        renderSummary(data);
        renderTopTables(data);
        renderChart(data);
    } catch (err) {
        console.error("대시보드 초기화 실패:", err);
    }

    const forecastBtn = document.getElementById("btn-load-forecast");
    if (forecastBtn) {
        forecastBtn.addEventListener("click", handleForecastClick);
    }
});
