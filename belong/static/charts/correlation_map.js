// belong/static/charts/correlation_map.js

// 모달용 / 카드용 차트를 따로 관리
let corrHeatmapChartModal = null;
let corrHeatmapChartInline = null;

document.addEventListener("DOMContentLoaded", () => {
    const mapContainer = document.getElementById("map-container");
    const mapInner = document.getElementById("map-inner");
    if (mapContainer && mapInner) {
        const svg = mapInner.querySelector("svg");
        if (!svg) {
            console.warn("[corr] SVG를 찾을 수 없습니다.");
        } else {
            // 필요하면 줌/드래그 활성화
            // initPanZoom(mapContainer, svg);
            setupRegionInteractions(svg);
        }
    }

    // 👉 오른쪽 '알고 가세요!' 카드용 폼 이벤트
    const guForm  = document.getElementById("corrGuForm");
    const guInput = document.getElementById("corrGuInput");
    const guError = document.getElementById("corrGuError");

    if (guForm && guInput) {
        guForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const guName = guInput.value.trim();

            if (!guName) {
                if (guError) {
                    guError.textContent = "구 이름을 입력해주세요. 예: 강남구, 도봉구";
                    guError.style.display = "block";
                }
                return;
            }
            if (guError) guError.style.display = "none";

            try {
                await fetchAndRenderHeatmap(guName, "corrHeatmapInlineCanvas");
            } catch (err) {
                console.error("[corr] inline heatmap error:", err);
                if (guError) {
                    guError.textContent = "데이터를 불러오지 못했습니다. 구 이름을 다시 확인해주세요.";
                    guError.style.display = "block";
                }
            }
        });
    }
});

/**
 * 🧭 path id → 한글 구 이름 매핑
 */
const GU_BY_ID = {
    "Dobong-gu": "도봉구",
    "Dongdaemun-gu": "동대문구",
    "Dongjak-gu": "동작구",
    "Eunpyeong-gu": "은평구",
    "Gangbuk-gu": "강북구",
    "Gangdong-gu": "강동구",
    "Gangseo-gu": "강서구",
    "Geumcheon-gu": "금천구",
    "Guro-gu": "구로구",
    "Gwanak-gu": "관악구",
    "Gwangjin-gu": "광진구",
    "Gangnam-gu": "강남구",
    "Jongno-gu": "종로구",
    "Jung-gu": "중구",
    "Jungnang-gu": "중랑구",
    "Mapo-gu": "마포구",
    "Nowon-gu": "노원구",
    "Seocho-gu": "서초구",
    "Seodaemun-gu": "서대문구",
    "Seongbuk-gu": "성북구",
    "Seongdong-gu": "성동구",
    "Songpa-gu": "송파구",
    "Yangcheon-gu": "양천구",
    "Yeongdeungpo-gu_1_": "영등포구",
    "Yongsan-gu": "용산구",
};

/**
 * (옵션) 드래그 + 줌
 */
function initPanZoom(container, svg) {
    let scale = 0.9;
    let translateX = 0;
    let translateY = 0;
    let isPanning = false;
    let startX = 0;
    let startY = 0;

    svg.style.transformOrigin = "50% 50%";
    applyTransform();

    function applyTransform() {
        svg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }

    container.addEventListener("wheel", (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 1.1 : 0.9;
        const newScale = Math.min(2.5, Math.max(0.5, scale * delta));
        scale = newScale;
        applyTransform();
    });

    container.addEventListener("mousedown", (e) => {
        e.preventDefault();
        isPanning = true;
        startX = e.clientX - translateX;
        startY = e.clientY - translateY;
    });

    window.addEventListener("mousemove", (e) => {
        if (!isPanning) return;
        translateX = e.clientX - startX;
        translateY = e.clientY - startY;
        applyTransform();
    });

    window.addEventListener("mouseup", () => {
        isPanning = false;
    });
}

/**
 * 🖱 SVG 각 구(path)에 hover / click 이벤트 연결
 */
function setupRegionInteractions(svg) {
    const paths = svg.querySelectorAll("path[id]");
    if (!paths.length) {
        console.warn("[corr] id 가진 path가 없습니다.");
        return;
    }

    const modalEl    = document.getElementById("corrModal");
    const modalTitle = document.getElementById("corrModalLabel");
    const modal      = modalEl ? new bootstrap.Modal(modalEl) : null;

    if (modalEl && modal) {
        const closeBtn = document.getElementById("corrModalClose");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => modal.hide());
        }
    }

    paths.forEach((regionPath) => {
        const id = regionPath.id;
        const gu = GU_BY_ID[id];
        if (!gu) return; // 구가 아닌 path는 스킵

        regionPath.style.cursor = "pointer";
        regionPath.style.transition = "fill 0.15s";

        regionPath.addEventListener("mouseenter", () => {
            regionPath.dataset.originalFill = regionPath.getAttribute("fill") || "#e5e5e5";
            regionPath.setAttribute("fill", "#c9defa");
        });

        regionPath.addEventListener("mouseleave", () => {
            const original = regionPath.dataset.originalFill || "#e5e5e5";
            regionPath.setAttribute("fill", original);
        });

        regionPath.addEventListener("click", async () => {
            console.log("[corr] click:", id, gu);
            if (!modal) return;

            if (modalTitle) {
                modalTitle.textContent = `${gu} 상관관계 히트맵`;
            }

            try {
                await fetchAndRenderHeatmap(gu, "corrHeatmapCanvas");
                modal.show();
            } catch (err) {
                console.error("[corr] modal heatmap error:", err);
                alert("해당 구의 상관관계 데이터를 불러오지 못했습니다.");
            }
        });
    });

    console.log("[corr] usable regions:", Object.keys(GU_BY_ID).length);
}

/**
 * 📊 /api/elderly/correlation → 히트맵 렌더링
 *  - guName: 그래프 제목에 표시할 구 이름 (region_name 으로 전달)
 *  - canvasId: 그릴 canvas id ("corrHeatmapCanvas" / "corrHeatmapInlineCanvas")
 */
async function fetchAndRenderHeatmap(guName, canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn("[corr] canvas 없음:", canvasId);
        return;
    }

    const params = new URLSearchParams();
    params.set("region_name", guName);
    params.set("year_from", "2017");
    params.set("year_to", "2023");

    const res = await fetch(`/api/elderly/correlation?${params.toString()}`);
    if (!res.ok) {
        throw new Error("API 응답 오류: HTTP " + res.status);
    }

    const json = await res.json();

    // 에러 응답 처리
    if (json.error || json.status === "error") {
        console.warn("[corr] API error:", json);
        throw new Error(json.message || "API error");
    }

    const data = json.data || {};
    let features = [];

    // 1) features 배열이 있으면 그걸 우선 사용
    if (Array.isArray(data.features) && data.features.length) {
        features = data.features;
    }
    // 2) 아니면 correlations + feature_desc 조합해서 사용
    else if (Array.isArray(data.correlations) && data.correlations.length) {
        const desc = data.feature_desc || {};
        features = data.correlations.map((c) => ({
            feature: c.feature,
            corr: c.corr,
            label: desc[c.feature] || c.feature,
        }));
    }

    if (!features.length) {
        console.warn("[corr] 상관관계 데이터가 비어있음");
        throw new Error("no correlation data");
    }

    const labels = features.map(
        (f) =>
            f.label ||
            (data.feature_desc && data.feature_desc[f.feature]) ||
            f.feature
    );
    const values = features.map((f) => f.corr ?? 0);

    const ctx = canvas.getContext("2d");

    // 어디에 그리는지에 따라 차트 인스턴스 선택
    if (canvasId === "corrHeatmapInlineCanvas") {
        if (corrHeatmapChartInline) corrHeatmapChartInline.destroy();
    } else {
        if (corrHeatmapChartModal) corrHeatmapChartModal.destroy();
    }

    // corr 값에 따라 색 농도
    const colors = values.map((v) => {
        const t = Math.max(-1, Math.min(1, v));
        const abs = Math.abs(t);
        const alpha = 0.2 + 0.6 * abs; // 0.2 ~ 0.8
        if (t >= 0) return `rgba(54, 162, 235, ${alpha})`;
        return `rgba(255, 99, 132, ${alpha})`;
    });

    const chart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "상관계수",
                    data: values,
                    backgroundColor: colors,
                },
            ],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    min: -1,
                    max: 1,
                    ticks: { stepSize: 0.2 },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) =>
                            `상관계수: ${ctx.parsed.x.toFixed(3)}`,
                    },
                },
                title: {
                    display: true,
                    text: `${guName} 고독사 관련 주요 지표 상관관계`,
                },
            },
        },
    });

    if (canvasId === "corrHeatmapInlineCanvas") {
        corrHeatmapChartInline = chart;
    } else {
        corrHeatmapChartModal = chart;
    }

    console.log("[corr] chart created on", canvasId);
}
