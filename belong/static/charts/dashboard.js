// =========================
// 1) 대시보드 API 호출
// =========================
async function fetchDashboard() {
    try {
        const res = await fetch("/api/elderly/population");

        if (!res.ok) {
            throw new Error("대시보드 API 호출 실패");
        }

        const json = await res.json();

        // 백엔드 협업자 포맷:
        // { "status": "success", "data": [ {...}, {...} ] }
        if (!json || !json.data) {
            throw new Error("대시보드 데이터 형식 오류");
        }

        return json.data;

    } catch (err) {
        console.error("Dashboard API 실패:", err);
        return [];    // 안전 fallback
    }
}


// =========================
// 2) DOMContentLoaded → 초기 렌더링
// =========================
document.addEventListener("DOMContentLoaded", async () => {

    const data = await fetchDashboard();

    if (!data || data.length === 0) {
        console.warn("대시보드 데이터 없음");
        return;
    }

    // 🔹 Summary 계산
    const total = data.reduce((sum, r) => sum + r.latest_value, 0);
    document.getElementById("summary-total").innerText = total.toLocaleString();

    const sorted = [...data].sort((a, b) => b.growth_rate - a.growth_rate);

    document.getElementById("summary-growth-top").innerText = sorted[0].region;
    document.getElementById("summary-growth-bottom").innerText =
        sorted[sorted.length - 1].region;

    // =========================
    // 3) Table 렌더링
    // =========================
    const tbody = document.getElementById("population-table-body");
    tbody.innerHTML = "";

    data.forEach(row => {
        tbody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${row.latest_value.toLocaleString()}</td>
                <td>${row.growth_rate}</td>
                <td>
                    <a href="/region/${row.region}" class="btn btn-sm btn-outline-primary">
                        상세보기
                    </a>
                </td>
            </tr>
        `;
    });


    // =========================
    // 4) Chart.js 렌더링
    // =========================

    // API 포맷: row.values = [{year: 2017, value: 5800}, ...]
    if (!data[0] || !data[0].values) {
        console.error("차트용 데이터 없음");
        return;
    }

    const ctx = document.getElementById("dashboard-chart").getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: data[0].values.map(v => v.year),
            datasets: data.map(regionRow => ({
                label: regionRow.region,
                data: regionRow.values.map(v => v.value),
                borderWidth: 2,
                tension: 0.25
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
});
