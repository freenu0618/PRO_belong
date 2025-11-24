document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("heatmap");
    const ctx = canvas.getContext("2d");

    ctx.font = "20px Arial";
    ctx.fillText("🔧 Heatmap 데이터는 모델 연동 후 표시됩니다.", 20, 50);
});
