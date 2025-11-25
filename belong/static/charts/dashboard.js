// =========================
// 1) API 호출 함수
// =========================
async function fetchDashboard() {
    const res = await fetch("/api/elderly/population");

    if (!res.ok) {
        throw new Error("대시보드 API 호출 실패");
    }

    const json = await res.json();

    // 백엔드 형식: { status: "success", data: [...] }
    if (!json || !json.data) {
        throw new Error("대시보드 데이터 형식 오류");
    }

    return json.data;   // 배열
}

// =========================
// 2) 메인 진입
// =========================
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const data = await fetchDashboard();

        if (!Array.isArray(data) || data.length === 0) {
            console.warn("대시보드 데이터가 비어 있습니다.");
            return;
        }

        renderSummaryCards(data);
        renderTable(data);
        renderChart(data);

    } catch (e) {
        console.error("Dashboard 로딩 실패:", e);
        const tbody = document.getElementById("population-table-body");
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-danger fw-bold">
                        대시보드 데이터를 불러오지 못했습니다.
                    </td>
                </tr>
            `;
        }
    }
});


// =========================
// 3) Summary 카드 렌더링
// =========================
function renderSummaryCards(data) {
    // 총 노인 인구 합
    const total = data.reduce((sum, r) => sum + (r.latest_value || 0), 0);
    const totalEl = document.getElementById("summary-total");
    if (totalEl) {
        totalEl.innerText = total.toLocaleString();
    }

    // 증가율 기준 정렬 (growth_rate 내림차순)
    const sorted = [...data].sort((a, b) => (b.growth_rate || 0) - (a.growth_rate || 0));

    const topRegion = sorted[0];
    const bottomRegion = sorted[sorted.length - 1];

    const topEl = document.getElementById("summary-growth-top");
    const bottomEl = document.getElementById("summary-growth-bottom");

    if (topEl && topRegion) {
        topEl.innerText = `${topRegion.region} (${(topRegion.growth_rate || 0).toFixed(1)}%)`;
    }
    if (bottomEl && bottomRegion) {
        bottomEl.innerText = `${bottomRegion.region} (${(bottomRegion.growth_rate || 0).toFixed(1)}%)`;
    }
}


// =========================
// 4) 테이블 렌더링
// =========================
function renderTable(data) {
    const tbody = document.getElementById("population-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    data.forEach(row => {
        const region = row.region || "-";
        const latest = row.latest_value || 0;
        const growth = row.growth_rate || 0;

        // 기본 예측 연도: 마지막 year + 1 (있으면)
        let defaultYear = "";
        if (Array.isArray(row.value) && row.value.length > 0) {
            const lastYear = row.value[row.value.length - 1].year;
            defaultYear = lastYear ? lastYear + 1 : "";
        }

        const detailUrl = defaultYear
            ? `/region/${region}?year=${defaultYear}`
            : `/region/${region}`;

        tbody.innerHTML += `
            <tr>
                <td>${region}</td>
                <td>${latest.toLocaleString()}</td>
                <td>${growth.toFixed ? growth.toFixed(1) : growth}%</td>
                <td>
                    <a href="${detailUrl}" class="btn btn-sm btn-outline-primary">
                        상세보기
                    </a>
                </td>
            </tr>
        `;
    });
}


// =========================
// 5) 차트 렌더링
// =========================
let dashboardChartInstance = null;

function renderChart(data) {
    const canvas = document.getElementById("dashboard-chart");
    if (!canvas) return;

    // 첫 지역의 연도 배열을 기준 라벨로 사용
    const firstRow = data[0];

    if (!firstRow || !Array.isArray(firstRow.value) || firstRow.value.length === 0) {
        console.warn("차트 데이터가 부족합니다.");
        return;
    }

    const labels = firstRow.value.map(v => v.year);

    const datasets = data.map(row => {
        const series = Array.isArray(row.value)
            ? row.value.map(v => v.value)
            : [];

        return {
            label: row.region,
            data: series,
            borderWidth: 2,
            fill: false,
            tension: 0.2
        };
    });

    if (dashboardChartInstance) {
        dashboardChartInstance.destroy();
    }

    const ctx = canvas.getContext("2d");

    dashboardChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom"
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}
