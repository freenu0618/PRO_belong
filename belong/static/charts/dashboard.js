// ----------------------------------------------------
// 1) 대시보드 API 호출
// ----------------------------------------------------
async function fetchDashboard() {
    try {
        const res = await fetch("/api/elderly/population");
        if (!res.ok) throw new Error("API 오류");
        return await res.json();
    } catch (e) {
        console.error("Dashboard API 실패:", e);
        return { data: [] }; // 안전 fallback
    }
}

// ----------------------------------------------------
// 2) DOM 로드 후 실행
// ----------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {

    const { data } = await fetchDashboard();

    // ---------------------------------------------
    // (A) 데이터 없는 경우 안전 처리
    // ---------------------------------------------
    if (!data || data.length === 0) {
        console.warn("대시보드 데이터가 비어있습니다.");
        document.getElementById("summary-total").innerText = "-";
        document.getElementById("summary-growth-top").innerText = "-";
        document.getElementById("summary-growth-bottom").innerText = "-";
        return;
    }

    // ---------------------------------------------
    // (B) Summary 영역 계산
    // ---------------------------------------------
    const total = data.reduce((sum, r) => sum + (r.latest_value || 0), 0);
    document.getElementById("summary-total").innerText = total.toLocaleString();

    const sorted = [...data].sort((a, b) => b.growth_rate - a.growth_rate);
    document.getElementById("summary-growth-top").innerText = sorted[0]?.region || "-";
    document.getElementById("summary-growth-bottom").innerText = sorted[sorted.length - 1]?.region || "-";

    // ---------------------------------------------
    // (C) 테이블 렌더링
    // ---------------------------------------------
    const tbody = document.getElementById("population-table-body");
    tbody.innerHTML = "";

    data.forEach(row => {
        tbody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${row.latest_value?.toLocaleString() ?? "-"}</td>
                <td>${row.growth_rate ?? "-"}%</td>
                <td>
                    <a href="/region/${row.region}" class="btn btn-sm btn-outline-primary">
                        상세보기
                    </a>
                </td>
            </tr>
        `;
    });

    // ---------------------------------------------
    // (D) Chart.js 렌더링 (안전 처리 포함)
    // ---------------------------------------------
    const firstRegion = data[0];

    if (!firstRegion || !firstRegion.values || firstRegion.values.length === 0) {
        console.warn("chart 데이터를 찾을 수 없어 차트를 그리지 않습니다.");
        return;
    }

    const ctx = document.getElementById("dashboard-chart").getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: firstRegion.values.map(v => v.year),
            datasets: data.map(r => ({
                label: r.region,
                data: (r.values || []).map(v => v.value),
                borderWidth: 1
            }))
        }
    });
});
