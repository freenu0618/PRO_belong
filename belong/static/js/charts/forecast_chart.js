document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById('forecastChart');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ["2019", "2020", "2021", "2022", "2023"],
            datasets: [{
                label: "예측 위험도",
                data: [2, 3, 4, 5, 7],
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
});
