// belong/static/charts/correlation_map.js

let corrHeatmapChart = null;

document.addEventListener("DOMContentLoaded", () => {
    const mapContainer = document.getElementById("map-container");
    const mapInner = document.getElementById("map-inner");
    if (!mapContainer || !mapInner) return;

    const svg = mapInner.querySelector("svg");
    if (!svg) {
        console.warn("[corr] SVG를 찾을 수 없습니다.");
        return;
    }

    // initPanZoom(mapContainer, svg);
    setupRegionInteractions(svg);
});

/**
 * 🧭 path id → 한글 구 이름 매핑
 *  👉 여기 id 값은 DevTools에서 path 선택했을 때 보이는 그대로 써야 함
 *     (예: id="Dobong-gu" 라고 되어있으면 키도 "Dobong-gu")
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
    "Yeongdeungpo-gu_1_": "영등포구",  // id에 _1_ 붙어있을 가능성 큼
    "Yongsan-gu": "용산구",
    // 혹시 다른 id가 있으면 여기 계속 추가
};

/**
 * 🔍 드래그(이동) + 휠 줌
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
 * 🖱 각 구 path에 hover / click 이벤트 연결
 *  - hover: 색 변경
 *  - click: 모달 열고 히트맵 렌더링
 */
function setupRegionInteractions(svg) {
    const paths = svg.querySelectorAll("path[id]");
    if (!paths.length) {
        console.warn("[corr] id 가진 path가 없습니다.");
        return;
    }

    const modalEl = document.getElementById("corrModal");
    const modalTitle = document.getElementById("corrModalLabel");
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;
    if (modalEl && modal) {
        const closeBtn = document.getElementById("corrModalClose");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                modal.hide();
            });
        }
    }
    paths.forEach((region) => {
        const id = region.id;
        const gu = GU_BY_ID[id];
        if (!gu) {
            // 외곽선 등은 id는 있지만 구가 아니면 스킵
            return;
        }

        region.style.cursor = "pointer";
        region.style.transition = "fill 0.15s";

        region.addEventListener("mouseenter", () => {
            region.dataset.originalFill = region.getAttribute("fill") || "#e5e5e5";
            region.setAttribute("fill", "#c9defa");
        });

        region.addEventListener("mouseleave", () => {
            const original = region.dataset.originalFill || "#e5e5e5";
            region.setAttribute("fill", original);
        });

        region.addEventListener("click", async () => {
            console.log("[corr] click:", id, gu);
            if (!modal) return;

            if (modalTitle) {
                modalTitle.textContent = `${gu} 상관관계 히트맵`;
            }

            await fetchAndRenderHeatmap(gu);
            modal.show();
        });
    });

    console.log("[corr] usable regions:", Object.keys(GU_BY_ID).length);
}

/**
 * 📊 /api/elderly/correlation 결과로 히트맵(가로 막대) 렌더링
 *  백엔드 JSON 예시(협력자가 준 구조):
 *  {
 *    "data": {
 *      "correlations": [{ "feature":"age_65_over", "corr":0.9989 }, ...],
 *      "feature_desc": {
 *         "age_65_over": "65세 이상 노인 수",
 *         ...
 *      },
 *      "features": [
 *        { "feature":"age_65_over", "label":"65세 이상 노인 수",
 *          "corr":0.9989, "vif":6.8995, "coef_std":1.0038, "selected":true
 *        },
 *        ...
 *      ]
 *    }
 *  }
 */
async function fetchAndRenderHeatmap(guName) {
    const canvas = document.getElementById("corrHeatmapCanvas");
    if (!canvas) {
        console.warn("[corr] corrHeatmapCanvas 캔버스 없음");
        return;
    }

    try {
        const res = await fetch("/api/elderly/correlation");
        if (!res.ok) throw new Error("API 응답 오류");

        const json = await res.json();
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
            return;
        }

        const labels = features.map(
            (f) =>
                f.label ||
                (data.feature_desc && data.feature_desc[f.feature]) ||
                f.feature
        );
        const values = features.map((f) => f.corr ?? 0);

        const ctx = canvas.getContext("2d");

        if (corrHeatmapChart) {
            corrHeatmapChart.destroy();
        }

        // corr 값에 따라 색 농도 다르게 (양수: 파랑, 음수: 빨강)
        const colors = values.map((v) => {
            const t = Math.max(-1, Math.min(1, v));
            const abs = Math.abs(t);
            const alpha = 0.2 + 0.6 * abs; // 0.2 ~ 0.8
            if (t >= 0) return `rgba(54, 162, 235, ${alpha})`;
            return `rgba(255, 99, 132, ${alpha})`;
        });

        corrHeatmapChart = new Chart(ctx, {
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
                        text: `${guName} 주요 지표 상관관계`,
                    },
                },
            },
        });
    } catch (err) {
        console.error("[corr] 히트맵 렌더링 실패:", err);
    }
}
