async function fetchDashboard() {
    try {
        const res = await fetch("/api/v1/elderly/population");
        if (!res.ok) throw new Error("API 오류");
        return await res.json();
    } catch (e) {
        console.error("Dashboard API 실패:", e);
        return { data: [] };
    }
}

document.addEventListener("DOMContentLoaded", async () => {

    const { data } = await fetchDashboard();

    // Summary
    const total = data.reduce((sum, r) => sum + r.latest_value, 0);
    document.getElementById("summary-total").innerText = total.toLocaleString();

    // Growth
    const sorted = [...data].sort((a, b) => b.growth_rate - a.growth_rate);
    document.getElementById("summary-growth-top").innerText = sorted[0].region;
    document.getElementById("summary-growth-bottom").innerText = sorted[sorted.length - 1].region;

    // Table
    const tbody = document.getElementById("population-table-body");
    tbody.innerHTML = "";

    data.forEach(row => {
        tbody.innerHTML += `
            <tr>
                <td>${row.region}</td>
                <td>${row.latest_value.toLocaleString()}</td>
                <td>${row.growth_rate}%</td>
                <td>
                    <a href="/region/${row.region}" class="btn btn-sm btn-outline-primary">
                        상세보기
                    </a>
                </td>
            </tr>
        `;
    });

    // Chart
    const ctx = document.getElementById("dashboard-chart").getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: data[0].values.map(v => v.year),
            datasets: data.map(r => ({
                label: r.region,
                data: r.values.map(v => v.value),
                borderWidth: 1
            }))
        }
    });
});
