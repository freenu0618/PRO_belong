// belong/static/js/correlation_map.js

window.addEventListener("DOMContentLoaded", () => {
    const mapContainer = document.getElementById("map-container");
    const mapInner = document.getElementById("map-inner");
    if (!mapContainer || !mapInner) return;

    const svg = mapInner.querySelector("svg");
    if (!svg) return;

    // -----------------------------
    // Tooltip 생성
    // -----------------------------
    const tooltip = document.createElement("div");
    tooltip.id = "map-tooltip";
    document.body.appendChild(tooltip);

    // -----------------------------
    // 1) SVG path <-> 구 이름 자동 매핑
    //    (텍스트 위치 기준으로 가장 가까운 path에 data-gu 부여)
    // -----------------------------
    const labelInfos = Array.from(svg.querySelectorAll("text")).map((t) => {
        const box = t.getBBox();
        return {
            el: t,
            name: t.textContent.trim(),
            x: box.x + box.width / 2,
            y: box.y + box.height / 2,
        };
    });

    // fill="none" 인 바깥 윤곽 path는 제외 (클릭 불필요)
    const guPaths = Array.from(svg.querySelectorAll("path")).filter((p) => {
        const fill = p.getAttribute("fill");
        return fill && fill.toLowerCase() !== "none";
    });

    guPaths.forEach((p) => {
        const box = p.getBBox();
        const cx = box.x + box.width / 2;
        const cy = box.y + box.height / 2;

        let best = null;
        let bestDist = Infinity;
        labelInfos.forEach((lab) => {
            const dx = lab.x - cx;
            const dy = lab.y - cy;
            const d2 = dx * dx + dy * dy;
            if (d2 < bestDist) {
                bestDist = d2;
                best = lab;
            }
        });

        if (best) {
            p.dataset.gu = best.name; // data-gu="강남구"
        }
    });

    // -----------------------------
    // 2) 줌(휠) / 팬(드래그)
    // -----------------------------
    let scale = 1.0;
    let panX = 0;
    let panY = 0;
    let isPanning = false;
    let startX = 0;
    let startY = 0;

    function applyTransform() {
        svg.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
    }

    mapInner.addEventListener("wheel", (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        const newScale = Math.min(3.0, Math.max(0.8, scale + delta));
        if (newScale === scale) return;
        scale = newScale;
        applyTransform();
    });

    mapInner.addEventListener("mousedown", (e) => {
        isPanning = true;
        mapInner.classList.add("grabbing");
        startX = e.clientX - panX;
        startY = e.clientY - panY;
    });

    window.addEventListener("mousemove", (e) => {
        if (!isPanning) return;
        panX = e.clientX - startX;
        panY = e.clientY - startY;
        applyTransform();
    });

    window.addEventListener("mouseup", () => {
        isPanning = false;
        mapInner.classList.remove("grabbing");
    });

    // -----------------------------
    // 3) 상관관계 API 호출 (/api/elderly/correlation)
    //    백엔드 협업자가 준 JSON 형식에 맞춤
    // -----------------------------
    async function fetchCorrelation(guName) {
        const params = new URLSearchParams();
        // 현재 백엔드 compute()가 region은 안 쓰더라도,
        // 나중 확장 대비해서 region 쿼리만 붙여서 보냄 (무시하면 그만)
        params.set("region", guName);

        const res = await fetch(`/api/elderly/correlation?` + params.toString());
        if (!res.ok) {
            throw new Error("상관관계 API 호출 실패");
        }
        const json = await res.json();
        if (!json || json.status !== "success") {
            throw new Error("상관관계 데이터 형식 오류");
        }

        const data = json.data;

        // 기대하는 구조:
        // {
        //   target: "elderly_population",
        //   vif_threshold: 10.0,
        //   features: [
        //     { feature, label, corr, vif, coef_std, selected },
        //     ...
        //   ],
        //   correlations: [...],
        //   feature_desc: {...}
        // }
        return {
            target: data.target,
            vifThreshold: data.vif_threshold,
            features: data.features || [],
            featureDesc: data.feature_desc || {},
        };
    }

    // -----------------------------
    // 4) corr 값에 따른 색깔 (히트맵용 1열)
    // -----------------------------
    function getHeatColor(value) {
        const v = Math.max(-1, Math.min(1, value));
        if (v >= 0) {
            const t = v;
            const r = 255;
            const g = Math.round(255 * (1 - t * 0.6));
            const b = Math.round(255 * (1 - t));
            return `rgb(${r},${g},${b})`;
        } else {
            const t = -v;
            const r = Math.round(255 * (1 - t));
            const g = Math.round(255 * (1 - t * 0.6));
            const b = 255;
            return `rgb(${r},${g},${b})`;
        }
    }

    // -----------------------------
    // 5) 모달에 테이블 렌더링
    //    (타깃 vs 각 피처의 상관계수 + VIF + 선택 여부)
    // -----------------------------
    function openCorrelationModal(guName, payload) {
        const { target, vifThreshold, features } = payload;

        const modalTitle = document.getElementById("corrModalLabel");
        const container = document.getElementById("heatmapContainer");

        modalTitle.textContent = `${guName} 상관관계 (타겟: ${target})`;

        const table = document.createElement("table");
        table.className = "table heatmap-table";

        const thead = document.createElement("thead");
        const headRow = document.createElement("tr");
        ["변수명", "라벨", "상관계수", "VIF", "선택여부"].forEach((h) => {
            const th = document.createElement("th");
            th.textContent = h;
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        (features || []).forEach((f) => {
            const tr = document.createElement("tr");

            const nameTd = document.createElement("td");
            nameTd.textContent = f.feature;

            const labelTd = document.createElement("td");
            labelTd.textContent = f.label || f.feature;

            const corrTd = document.createElement("td");
            const corrVal = f.corr;
            const corrNum =
                typeof corrVal === "number" ? corrVal : parseFloat(corrVal);
            corrTd.textContent = isNaN(corrNum) ? "" : corrNum.toFixed(2);
            if (!isNaN(corrNum)) {
                const color = getHeatColor(corrNum);
                corrTd.style.backgroundColor = color;
                corrTd.style.color =
                    Math.abs(corrNum) > 0.6 ? "#fff" : "#000";
            }

            const vifTd = document.createElement("td");
            if (f.vif === null || f.vif === undefined) {
                vifTd.textContent = "-";
            } else {
                const vifNum =
                    typeof f.vif === "number" ? f.vif : parseFloat(f.vif);
                vifTd.textContent = isNaN(vifNum)
                    ? "-"
                    : vifNum.toFixed(2);

                if (!isNaN(vifNum) && vifThreshold) {
                    if (vifNum > vifThreshold) {
                        vifTd.style.color = "#b02a37"; // 빨강
                        vifTd.style.fontWeight = "600";
                    }
                }
            }

            const selTd = document.createElement("td");
            selTd.textContent = f.selected ? "✔" : "";

            [nameTd, labelTd, corrTd, vifTd, selTd].forEach((td) =>
                tr.appendChild(td)
            );
            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        container.innerHTML = "";
        container.appendChild(table);

        const modalEl = document.getElementById("corrModal");
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    // -----------------------------
    // 6) 각 구 path 이벤트 (hover / click)
    // -----------------------------
    guPaths.forEach((area) => {
        const guName = area.dataset.gu || "알 수 없음";

        // hover: 툴팁 + 색 강조
        area.addEventListener("mousemove", (e) => {
            tooltip.textContent = guName;
            tooltip.style.left = e.pageX + 12 + "px";
            tooltip.style.top = e.pageY + 12 + "px";
            tooltip.style.display = "block";

            if (!area.dataset._origFill) {
                area.dataset._origFill = area.getAttribute("fill") || "#e5e5e5";
            }
            area.setAttribute("fill", "#cfe2ff");
        });

        area.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
            const orig = area.dataset._origFill || "#e5e5e5";
            area.setAttribute("fill", orig);
        });

        // click: 상관관계 테이블 모달
        area.addEventListener("click", async () => {
            try {
                const payload = await fetchCorrelation(guName);
                openCorrelationModal(guName, payload);
            } catch (err) {
                console.error(err);
                alert("상관관계 데이터를 불러오지 못했습니다.");
            }
        });
    });
});
