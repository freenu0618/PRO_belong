async function fetchCorrelation() {
    try {
        const res = await fetch("/api/elderly/correlation");

        if (!res.ok) throw new Error();

        return await res.json();
    } catch (e) {
        console.warn("API 실패 → mock 사용");
        return await fetch("/static/mock/correlation.json").then(r => r.json());
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    const { data } = await fetchCorrelation();

    // Table
    const tbody = document.getElementById("corr-table-body");
    tbody.innerHTML = "";

    data.correlations.forEach(row => {
        tbody.innerHTML += `
            <tr>
                <td>${row.feature}</td>
                <td>${data.feature_desc[row.feature]}</td>
                <td>${row.corr}</td>
            </tr>
        `;
    });

    // Heatmap
    const ctx = document.getElementById("heatmap-canvas").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.correlations.map(v => v.feature),
            datasets: [{
                data: data.correlations.map(v => v.corr),
                backgroundColor: "#0d6efd"
            }]
        }
    });
});
