// correlation_map.js

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

        // 가장 가까운 텍스트(구 이름)를 찾는다
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
            p.dataset.gu = best.name;  // data-gu="강남구" 형식으로 세팅
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
    // 3) 상관관계 API 호출
    // -----------------------------
    async function fetchCorrelation(guName) {
        // 미래 확장 대비: region, year_from, year_to 모두 쿼리 파라미터로 보낼 준비
        const params = new URLSearchParams();
        params.set("region", guName);  // 백엔드가 나중에 region 사용하면 됨

        const res = await fetch(`/api/elderly/correlation?` + params.toString());
        if (!res.ok) {
            throw new Error("상관관계 API 호출 실패");
        }
        const json = await res.json();
        if (!json || json.status !== "success") {
            throw new Error("상관관계 데이터 형식 오류");
        }

        let payload = json.data;

        // 1) data = { corr_matrix, corr_cols } 형태
        if (payload.corr_matrix && payload.corr_cols) {
            return {
                matrix: payload.corr_matrix,
                cols: payload.corr_cols,
            };
        }

        // 2) data = { housing: { corr_matrix, corr_cols }, ratio: ... } 형태
        if (payload.housing && payload.housing.corr_matrix) {
            return {
                matrix: payload.housing.corr_matrix,
                cols: payload.housing.corr_cols,
            };
        }

        throw new Error("지원하지 않는 상관관계 데이터 포맷");
    }

    // -----------------------------
    // 4) 히트맵 모달 렌더링
    // -----------------------------
    function getHeatColor(value) {
        const v = Math.max(-1, Math.min(1, value));
        if (v >= 0) {
            const t = v; // 0~1
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

    function openHeatmapModal(guName, corrMatrix, cols) {
        const modalTitle = document.getElementById("corrModalLabel");
        const container = document.getElementById("heatmapContainer");
        modalTitle.textContent = `${guName} 상관관계 히트맵`;

        const table = document.createElement("table");
        table.className = "table heatmap-table";

        const thead = document.createElement("thead");
        const headRow = document.createElement("tr");
        headRow.appendChild(document.createElement("th"));

        cols.forEach((c) => {
            const th = document.createElement("th");
            th.textContent = c;
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        cols.forEach((rowKey) => {
            const tr = document.createElement("tr");
            const rowHeader = document.createElement("th");
            rowHeader.textContent = rowKey;
            tr.appendChild(rowHeader);

            cols.forEach((colKey) => {
                const td = document.createElement("td");
                const v = corrMatrix[rowKey][colKey];
                const num = typeof v === "number" ? v : parseFloat(v);
                const display = isNaN(num) ? "" : num.toFixed(2);
                td.textContent = display;

                if (!isNaN(num)) {
                    const color = getHeatColor(num);
                    td.style.backgroundColor = color;
                    td.style.color = Math.abs(num) > 0.6 ? "#fff" : "#000";
                }

                tr.appendChild(td);
            });

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
    // 5) 각 구 path 이벤트 (hover / click)
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

        // click: 상관관계 히트맵 모달
        area.addEventListener("click", async () => {
            try {
                const { matrix, cols } = await fetchCorrelation(guName);
                openHeatmapModal(guName, matrix, cols);
            } catch (err) {
                console.error(err);
                alert("상관관계 데이터를 불러오지 못했습니다.");
            }
        });
    });
});
