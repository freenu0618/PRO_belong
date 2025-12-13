// belong/static/charts/correlation_map.js

// 모달용 / 카드용 차트를 따로 관리
let corrHeatmapChartModal = null;
let corrHeatmapChartInline = null;

// 현재 선택된 구(모달 '크게 보기' 등에서 재사용)
let corrCurrentGuName = "강남구";

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
  const guForm = document.getElementById("corrGuForm");
  const guInput = document.getElementById("corrGuInput");
  const guError = document.getElementById("corrGuError");

  if (guForm && guInput) {
    guForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const guName = guInput.value.trim();

      if (!guName) {
        if (guError) {
          guError.textContent = "구 이름을 입력해주세요.";
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
          guError.textContent =
            "데이터를 불러오지 못했습니다. 구 이름을 다시 확인해주세요.";
          guError.style.display = "block";
        }
      }
    });
  }

  // ✅ 초기 기본 렌더링 (빈 화면 방지)
  // - 처음 진입 시에도 카드 히트맵(가로 막대)이 보이도록 기본 구를 그려둡니다.
  // - input이 비어있으면 기본 구를 채워줍니다.
  const defaultGu = corrCurrentGuName;
  if (guInput && !guInput.value) guInput.value = defaultGu;

  // 인라인(카드) 차트 기본 표시
  if (document.getElementById("corrHeatmapInlineCanvas")) {
    fetchAndRenderHeatmap(defaultGu, "corrHeatmapInlineCanvas").catch((err) =>
      console.error("[corr] default inline render failed:", err)
    );
  }

  // '크게 보기' 버튼(bootstrap data-bs-toggle)로 열리는 모달에서도 자동 렌더링
  const modalElAuto = document.getElementById("corrModal");
  if (modalElAuto) {
    modalElAuto.addEventListener("shown.bs.modal", () => {
      fetchAndRenderHeatmap(corrCurrentGuName, "corrHeatmapCanvas").catch(
        (err) => console.error("[corr] modal render failed:", err)
      );
    });
  }
});

/**
 * 🧭 path id → 한글 구 이름 매핑
 *  (SVG에서 path의 id 값이 아래 키와 매칭되어야 클릭이 동작합니다)
 */
const GU_BY_ID = {
  "Dobong-gu": "도봉구",
  "Dongdaemun-gu": "동대문구",
  "Dongjak-gu": "동작구",
  "Eunpyeong-gu": "은평구",
  "Gangbuk-gu": "강북구",
  "Gangdong-gu": "강동구",
  "Gangnam-gu": "강남구",
  "Gangseo-gu": "강서구",
  "Geumcheon-gu": "금천구",
  "Guro-gu": "구로구",
  "Gwanak-gu": "관악구",
  "Gwangjin-gu": "광진구",
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

  const applyTransform = () => {
    svg.style.transformOrigin = "center center";
    svg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
  };

  applyTransform();

  container.addEventListener("wheel", (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.05 : 0.05;
    scale = Math.min(1.8, Math.max(0.6, scale + delta));
    applyTransform();
  });

  container.addEventListener("mousedown", (e) => {
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

  const modalEl = document.getElementById("corrModal");
  const modalTitle = document.getElementById("corrModalLabel");
  const modal = modalEl ? new bootstrap.Modal(modalEl) : null;

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
      regionPath.dataset.originalFill =
        regionPath.getAttribute("fill") || "#e5e5e5";
      regionPath.setAttribute("fill", "#c9defa");
    });

    regionPath.addEventListener("mouseleave", () => {
      const original = regionPath.dataset.originalFill || "#e5e5e5";
      regionPath.setAttribute("fill", original);
    });

    regionPath.addEventListener("click", async () => {
      if (!modalEl || !modal) {
        // 모달이 없으면 인라인만 갱신
        try {
          await fetchAndRenderHeatmap(gu, "corrHeatmapInlineCanvas");
        } catch (err) {
          console.error("[corr] inline click heatmap error:", err);
          alert("해당 구의 상관관계 데이터를 불러오지 못했습니다.");
        }
        return;
      }

      try {
        if (modalTitle) modalTitle.textContent = `${gu} 상관관계 히트맵`;
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
 * 📊 /api/elderly/correlation → 히트맵(가로 막대) 렌더링
 *  - guName: 제목에 표시할 구 이름 (region_name 으로 전달)
 *  - canvasId: 그릴 canvas id ("corrHeatmapCanvas" / "corrHeatmapInlineCanvas")
 */
async function fetchAndRenderHeatmap(guName, canvasId) {
  corrCurrentGuName = guName;

  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.warn("[corr] canvas 없음:", canvasId);
    return;
  }
  if (typeof Chart === "undefined") {
    console.error("[corr] Chart.js가 로드되지 않았습니다.");
    return;
  }

  // (캔버스 높이가 0으로 잡혀서 안 보이는 경우 방지)
  if (!canvas.style.height) {
    canvas.style.height =
      canvasId === "corrHeatmapInlineCanvas" ? "220px" : "360px";
  }

  // API 호출
  const params = new URLSearchParams();
  params.set("region_name", guName);

  const res = await fetch(`/api/elderly/correlation?${params.toString()}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);

  const data = await res.json();

  // 1) correlation_pairs가 있으면 그걸 우선 사용
  // 2) 아니면 correlations + feature_desc 조합해서 사용
  let labels = [];
  let values = [];

  if (Array.isArray(data.correlation_pairs) && data.correlation_pairs.length) {
    labels = data.correlation_pairs.map((p) => p.feature);
    values = data.correlation_pairs.map((p) => p.corr);
  } else if (Array.isArray(data.correlations) && data.correlations.length) {
    // correlations: [{feature, corr}, ...] 형태 가정
    labels = data.correlations.map((c) => c.feature || c.name || "unknown");
    values = data.correlations.map((c) => c.corr ?? c.value ?? 0);
  } else if (data.matrix && data.features) {
    // matrix/feature 기반이더라도 "고독사" 기준 벡터로 바꿔서 표시하는 용도
    // (여기서는 간단히 첫 번째 row를 사용)
    const f = data.features;
    const row = Array.isArray(data.matrix) ? data.matrix[0] : [];
    labels = f.slice(0);
    values = row.slice(0, labels.length).map((v) => Number(v) || 0);
  } else {
    throw new Error("no correlation data");
  }

  // 너무 길면 상위 15개만 (절대값 기준)
  const combined = labels
    .map((lab, i) => ({ lab, val: Number(values[i]) || 0 }))
    .sort((a, b) => Math.abs(b.val) - Math.abs(a.val))
    .slice(0, 15);

  labels = combined.map((x) => x.lab);
  values = combined.map((x) => x.val);

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
            label: (ctx) => `상관계수: ${ctx.parsed.x.toFixed(3)}`,
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
