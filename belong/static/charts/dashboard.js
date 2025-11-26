// =========================
// 공통 상태 / 헬퍼
// =========================
let dashboardData = [];
let sortedByGrowth = [];
let dashboardChart = null;
let tableExpanded = false;

// 공통 JSON fetch 헬퍼
async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
    }
    return await res.json();
}

// =========================
// 1) 대시보드 API 호출
// =========================
async function fetchDashboard() {
    try {
        const json = await fetchJson("/api/elderly/population");

        // 백엔드 포맷 1) { status, data: [...] }
        //          2) [ ... ] 그대로 오는 경우 둘 다 대응
        const data = Array.isArray(json) ? json : json.data;

        if (!data || !Array.isArray(data)) {
            throw new Error("대시보드 데이터 형식 오류");
        }

        return data;
    } catch (err) {
        console.error("Dashboard API 실패:", err);
        return []; // 안전 fallback
    }
}

// =========================
// 2) Summary 렌더링
// =========================
function renderSummary(sortedData) {
    if (!sortedData || sortedData.length === 0) return;

    const total = sortedData.reduce((sum, r) => sum + (r.latest_value || 0), 0);
    const top = sortedData[0];
    const bottom = sortedData[sortedData.length - 1];

    const totalEl = document.getElementById("summary-total");
    const topEl = document.getElementById("summary-growth-top");
    const bottomEl = document.getElementById("summary-growth-bottom");

    if (totalEl) {
        totalEl.innerText = total.toLocaleString("ko-KR");
    }
    if (topEl && top) {
        topEl.innerText = top.region;
    }
    if (bottomEl && bottom) {
        bottomEl.innerText = bottom.region;
    }
}

// =========================
// 3) Table 렌더링 (Top N + 더보기)
// =========================
function renderTable(limit) {
    const tbody = document.getElementById("population-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    const targetList = limit
        ? sortedByGrowth.slice(0, Math.min(limit, sortedByGrowth.length))
        : sortedByGrowth;

    targetList.forEach(row => {
        const latest = row.latest_value ?? 0;
        const growth = row.growth_rate ?? 0;
        tbody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${latest.toLocaleString("ko-KR")}</td>
                <td>${(growth * 100).toFixed(2)}%</td>
                <td>
                    <a href="/region/${encodeURIComponent(row.region)}" class="btn btn-sm btn-outline-primary">
                        상세보기
                    </a>
                </td>
            </tr>
        `;
    });

    const btn = document.getElementById("btn-toggle-table");
    if (btn) {
        btn.innerText = tableExpanded ? "접기" : "더보기";
    }
}

function toggleTable() {
    tableExpanded = !tableExpanded;
    if (tableExpanded) {
        renderTable(); // 전체
    } else {
        renderTable(5); // Top5
    }
}

// =========================
// 4) Chart.js 렌더링
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

    // values / value / history 중 있는 키를 사용 : 셋중 어떤게 들어와도 활성화
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
            datasets: datasets
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
async function handleForecastClick() {
    const input = document.getElementById("forecast-region-input");
    if (!input) return;

    const region = input.value.trim();
    if (!region) {
        alert("구 이름을 입력해 주세요. (예: 강남구)");
        input.focus();
        return;
    }

    try {
        const url = `/api/elderly/forecast/${encodeURIComponent(region)}`;
        const res = await fetch(url);
        let json = null;

        try {
            json = await res.json();
        } catch (e) {
            console.error("Forecast 응답 JSON 파싱 실패:", e);
        }

        if (!res.ok || !json || json.status === "error") {
            const msg =
                (json && json.message) ||
                "예측 데이터를 불러오지 못했습니다. (서버 오류)";
            // 에러도 모달로 보여주자
            openForecastModal(region, {
                message: msg,
                history: [],
                forecast: []
            });
            return;
        }

        const payload = json.data || json;
        openForecastModal(region, payload);
    } catch (err) {
        console.error("Forecast API 실패:", err);
        alert("예측 데이터를 불러오지 못했습니다. 네트워크 상태를 확인해 주세요.");
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

    // Bootstrap 모달 표시 {{super() }}를 추가했기 때문에 팝업처럼 뜨게 해줌
    if (window.bootstrap && bootstrap.Modal) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    } else {
        // Bootstrap이 없다면 임시로 그냥 보이게만 처리
        modalEl.style.display = "block";
    }
}

// =========================
// 6) 초기화
// =========================
document.addEventListener("DOMContentLoaded", async () => {
    // 1) 데이터 로드
    const data = await fetchDashboard();

    if (!data || data.length === 0) {
        console.warn("대시보드 데이터 없음");
        return;
    }

    dashboardData = data;
    sortedByGrowth = [...dashboardData].sort(
        (a, b) => (b.growth_rate || 0) - (a.growth_rate || 0)
    );

    // 2) Summary, Table(Top5), Chart 렌더링
    renderSummary(sortedByGrowth);
    renderTable(5);          // 기본: Top5만
    renderChart(dashboardData);

    // 3) 더보기 버튼
    const toggleBtn = document.getElementById("btn-toggle-table");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", toggleTable);
    }

    // 4) Forecast 버튼
    const forecastBtn = document.getElementById("btn-load-forecast");
    if (forecastBtn) {
        forecastBtn.addEventListener("click", handleForecastClick);
    }
});
