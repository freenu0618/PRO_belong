// belong/static/charts/correlation_chart.js

(function () {
    document.addEventListener("DOMContentLoaded", initCorrelationUI);

    let coefChart = null;
    let vifChart = null;

    function initCorrelationUI() {
        const startSel = document.getElementById("corrStartYear");
        const endSel   = document.getElementById("corrEndYear");
        const applyBtn = document.getElementById("corrApplyBtn");

        // 이 페이지가 아닐 수 있으니 방어
        if (!startSel || !endSel || !applyBtn) return;

        // 연도 셀렉트 채우기 (필요하면 숫자 범위만 바꿔서 쓰면 됨)
        const YEAR_MIN = 2015;
        const YEAR_MAX = 2023;
        for (let y = YEAR_MIN; y <= YEAR_MAX; y++) {
            const opt1 = new Option(String(y), String(y));
            const opt2 = new Option(String(y), String(y));
            startSel.appendChild(opt1);
            endSel.appendChild(opt2);
        }
        startSel.value = String(2017);
        endSel.value   = String(2023);

        // 적용 버튼 클릭 시
        applyBtn.addEventListener("click", () => {
            fetchCorrelationByUI();
        });

        // 첫 진입 시 한 번 호출 (원하면 주석 처리 가능)
        fetchCorrelationByUI();
    }

    // UI에서 값 읽어서 호출하는 공용 함수
    async function fetchCorrelationByUI() {
        const guSelect = document.getElementById("corrGuSelect");
        const startSel = document.getElementById("corrStartYear");
        const endSel   = document.getElementById("corrEndYear");

        if (!startSel || !endSel) return;

        let startYear = parseInt(startSel.value, 10);
        let endYear   = parseInt(endSel.value, 10);

        if (isNaN(startYear) || isNaN(endYear)) return;

        // 시작/종료가 뒤바뀌어 있으면 교환
        if (startYear > endYear) {
            [startYear, endYear] = [endYear, startYear];
            startSel.value = String(startYear);
            endSel.value   = String(endYear);
        }

        const region = guSelect ? guSelect.value : "";

        await fetchCorrelation(region, startYear, endYear);
    }

    // 실제 API 호출 함수
    async function fetchCorrelation(region, startYear, endYear) {
        try {
            const params = new URLSearchParams();
            if (startYear) params.append("year_from", String(startYear));
            if (endYear)   params.append("year_to",   String(endYear));
            if (region)    params.append("region",    region); // 백엔드에서 지원하면 사용, 아니면 무시됨

            const qs = params.toString();
            const url = qs ? `/api/elderly/correlation?${qs}` : "/api/elderly/correlation";

            const res = await fetch(url);
            if (!res.ok) {
                console.error("Correlation API 실패:", res.status, res.statusText);
                return;
            }

            const json = await res.json();

            // 백엔드 응답 형태: { status:"success", data:{...} } 또는 바로 {...}
            const payload = json.data || json;
            const features    = payload.features    || [];
            const correlations = payload.correlations || [];
            const featureDesc = payload.feature_desc || {};

            updateCharts(features);
            updateTable(features);
            updateSummaryText(features, featureDesc, correlations, region, startYear, endYear);
        } catch (err) {
            console.error("Correlation fetch 에러:", err);
        }
    }

    // ===== 그래프 렌더링 =====

    function updateCharts(features) {
        const ctxCoef = document.getElementById("corrCoefChart");
        const ctxVif  = document.getElementById("corrVifChart");
        if (!ctxCoef || !ctxVif) return;

        // 1) 영향력 그래프: selected == true 만
        const selected = features
            .filter(f => f.selected && typeof f.coef_std === "number")
            .sort((a, b) => Math.abs(b.coef_std) - Math.abs(a.coef_std));

        const coefLabels = selected.map(f => f.label || f.feature);
        const coefValues = selected.map(f => f.coef_std);

        // 2) VIF 그래프: 전체
        const vifLabels = features.map(f => f.label || f.feature);
        const vifValues = features.map(f => f.vif);

        // Chart.js 생성 또는 업데이트
        if (coefChart) {
            coefChart.data.labels = coefLabels;
            coefChart.data.datasets[0].data = coefValues;
            coefChart.update();
        } else {
            coefChart = new Chart(ctxCoef.getContext("2d"), {
                type: "bar",
                data: {
                    labels: coefLabels,
                    datasets: [{
                        label: "표준화 계수 β",
                        data: coefValues
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            zeroLineColor: "#000",
                            title: { display: true, text: "β (표준화 계수)" }
                        }
                    }
                }
            });
        }

        if (vifChart) {
            vifChart.data.labels = vifLabels;
            vifChart.data.datasets[0].data = vifValues;
            vifChart.update();
        } else {
            vifChart = new Chart(ctxVif.getContext("2d"), {
                type: "bar",
                data: {
                    labels: vifLabels,
                    datasets: [{
                        label: "VIF",
                        data: vifValues
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: { display: true, text: "VIF" }
                        }
                    }
                }
            });
        }
    }

    // ===== 테이블 렌더링 =====

    function updateTable(features) {
        const tbody = document.querySelector("#corrSummaryTable tbody");
        if (!tbody) return;

        const fmt = (v) =>
            typeof v === "number" && !isNaN(v) ? v.toFixed(3) : "-";

        tbody.innerHTML = "";
        features.forEach(f => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td>${f.label || f.feature}</td>
                <td>${fmt(f.corr)}</td>
                <td>${fmt(f.coef_std)}</td>
                <td>${fmt(f.vif)}</td>
                <td>${f.selected ? "●" : ""}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ===== 설명 문구 자동 생성 =====

    function updateSummaryText(features, featureDesc, correlations, region, startYear, endYear) {
        const el = document.getElementById("corrSummaryText");
        if (!el) return;

        if (!features || features.length === 0) {
            el.textContent = "선택하신 조건에서 상관관계 결과를 찾지 못했습니다.";
            return;
        }

        // selected == true 중 |coef_std| 큰 순으로 상위 2~3개
        const selected = features
            .filter(f => f.selected && typeof f.coef_std === "number")
            .sort((a, b) => Math.abs(b.coef_std) - Math.abs(a.coef_std))
            .slice(0, 3);

        if (selected.length === 0) {
            el.textContent = "선택된 주요 설명 변수가 없습니다. VIF나 상관관계를 함께 확인해 보세요.";
            return;
        }

        const sentences = selected.map(f => {
            const label = f.label || f.feature;
            const corr = typeof f.corr === "number" ? f.corr : 0;
            const beta = f.coef_std;
            const vif  = f.vif;

            const strength = (() => {
                const a = Math.abs(corr);
                if (a >= 0.7) return "매우 강한";
                if (a >= 0.5) return "강한";
                if (a >= 0.3) return "보통 수준의";
                return "약한";
            })();

            const sign = corr >= 0 ? "양의" : "음의";

            const vifComment =
                typeof vif === "number"
                    ? (vif < 5
                        ? `VIF=${vif.toFixed(2)}로 공선성 문제는 크지 않은 편입니다.`
                        : `VIF=${vif.toFixed(2)}로 공선성에 주의가 필요합니다.`)
                    : "";

            return `${label}는(은) 타깃과 ${strength} ${sign} 관계(β=${beta.toFixed(2)}, corr=${corr.toFixed(2)})를 보이며, ${vifComment}`;
        });

        const rangeText =
            startYear && endYear
                ? `${startYear}년~${endYear}년`
                : "선택한 기간";

        const regionText = region ? `${region}의 ` : "";

        el.textContent =
            `${rangeText} 기준으로 ${regionText}노인 인구와의 상관관계를 보면, ` +
            sentences.join(" ") ;
    }

})();
