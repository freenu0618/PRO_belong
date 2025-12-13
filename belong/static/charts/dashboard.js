/* belong/static/charts/dashboard.js
   Dashboard UI logic (Apple/Notion-ish UX)
   - Year range select
   - Region chips (max 2)
   - Seoul aggregate (sum across 25 gu) with toggle
   - Chart.js render for 2 slots x 4 charts
*/

(() => {
  // -----------------------------
  // 0) DOM helpers / constants
  // -----------------------------
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const SEOUL_LABEL = "서울시 전체";

  // DOM ids from your dashboard.html
  const elYearStart = $("#year-start");
  const elYearEnd = $("#year-end");
  const elRegionBox = $("#control-region-checkboxes");
  const elApplyBtn = $("#btn-apply-dashboard");
  const elToggleSeoul = $("#toggle-seoul"); // optional
  const elTitle1 = $("#region-title-1");
  const elTitle2 = $("#region-title-2");
  const elCol2 = $("#graph-column-2"); // slot2 column wrapper

  // Canvas IDs
  const CANVAS = {
    s1: {
      trendE: "trend-elderly-1",
      trendL: "trend-lonely-1",
      foreE: "forecast-elderly-1",
      foreL: "forecast-lonely-1",
    },
    s2: {
      trendE: "trend-elderly-2",
      trendL: "trend-lonely-2",
      foreE: "forecast-elderly-2",
      foreL: "forecast-lonely-2",
    },
  };

  // 기본 지역 리스트(서울 25개 구)
  const GU_LIST = [
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구",
    "동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구",
    "용산구","은평구","종로구","중구","중랑구"
  ];

  const DEFAULT_STATE = {
    ys: 2017,
    ye: 2023,
    regions: ["강남구", "종로구"], // 기본 2개
    includeSeoul: false,
  };

  // Chart.js guard
  if (!window.Chart) {
    console.error("[dashboard.js] Chart.js not found. Ensure Chart.js is loaded before dashboard.js");
  }

  // -----------------------------
  // 1) URL state (shareable)
  // -----------------------------
  function parseStateFromUrl() {
    const sp = new URLSearchParams(window.location.search);

    const ys = toInt(sp.get("ys"), DEFAULT_STATE.ys);
    const ye = toInt(sp.get("ye"), DEFAULT_STATE.ye);

    // r=강남구,종로구  or r=서울시 전체,강남구
    const r = sp.get("r");
    let regions = DEFAULT_STATE.regions.slice();
    if (r) {
      regions = r.split(",").map(x => decodeURIComponent(x.trim())).filter(Boolean);
      // sanitize: max 2
      regions = regions.slice(0, 2);
    }

    // includeSeoul is derived by selection
    const includeSeoul = regions.includes(SEOUL_LABEL);

    return {
      ys,
      ye,
      regions,
      includeSeoul,
    };
  }



  function writeStateToUrl(state) {
    const sp = new URLSearchParams(window.location.search);

    sp.set("ys", String(state.ys));
    sp.set("ye", String(state.ye));
    sp.set("r", state.regions.map(x => encodeURIComponent(x)).join(","));

    const newUrl = `${window.location.pathname}?${sp.toString()}`;
    window.history.replaceState({}, "", newUrl);
  }

  function toInt(v, fallback) {
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  }

  // -----------------------------
  // 2) Year selects
  // -----------------------------
  // 실제 데이터에서 year 범위를 동적으로 뽑는 게 최선이지만,
  // 초기 UX를 위해 기본 범위를 먼저 채워두고(2014~2028),
  // 이후 데이터 응답 기반으로 보정해도 됨.
  function initYearSelects(state) {
    if (!elYearStart || !elYearEnd) return;

    const minY = 2014;
    const maxY = 2028; // forecast 고려
    elYearStart.innerHTML = "";
    elYearEnd.innerHTML = "";

    for (let y = minY; y <= maxY; y++) {
      const opt1 = document.createElement("option");
      opt1.value = String(y);
      opt1.textContent = String(y);
      elYearStart.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = String(y);
      opt2.textContent = String(y);
      elYearEnd.appendChild(opt2);
    }

    elYearStart.value = String(state.ys);
    elYearEnd.value = String(state.ye);

    // UX: start > end 방지
    elYearStart.addEventListener("change", () => {
      const ys = Number(elYearStart.value);
      const ye = Number(elYearEnd.value);
      if (ys > ye) elYearEnd.value = String(ys);
    });
    elYearEnd.addEventListener("change", () => {
      const ys = Number(elYearStart.value);
      const ye = Number(elYearEnd.value);
      if (ye < ys) elYearStart.value = String(ye);
    });
  }

  // -----------------------------
  // 3) Region chips (with Seoul toggle)
  // -----------------------------
  function renderRegionChips(state) {
    if (!elRegionBox) return;

    elRegionBox.innerHTML = "";

    const items = [SEOUL_LABEL, ...GU_LIST];

    items.forEach((name) => {
      const label = document.createElement("label");
      label.className = "region-chip";

      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = name;

      if (state.regions.includes(name)) input.checked = true;

      const span = document.createElement("span");
      span.textContent = name;

      label.appendChild(input);
      label.appendChild(span);
      elRegionBox.appendChild(label);

      input.addEventListener("change", () => {
        // 토글 ON 상태에서 서울 해제 방지
        if (elToggleSeoul?.checked && name === SEOUL_LABEL && !input.checked) {
          input.checked = true;
          return;
        }

        // max 2
        const checked = getCheckedRegions();
        if (checked.length > 2) {
          input.checked = false;
          return;
        }

        // 서울 포함 토글 상태 동기화
        if (name === SEOUL_LABEL && elToggleSeoul) {
          elToggleSeoul.checked = input.checked;
        }
      });
    });

    // Toggle behavior
    if (elToggleSeoul) {
      elToggleSeoul.checked = state.regions.includes(SEOUL_LABEL);

      elToggleSeoul.addEventListener("change", () => {
        const seoulInput = elRegionBox.querySelector(`input[type="checkbox"][value="${SEOUL_LABEL}"]`);
        if (!seoulInput) return;

        if (elToggleSeoul.checked) {
          seoulInput.checked = true;

          // 서울 포함 시: 나머지는 최대 1개만 유지
          const checked = getCheckedRegions();
          if (checked.length > 2) {
            const nonSeoul = checked.filter(x => x !== SEOUL_LABEL);
            while (nonSeoul.length > 1) {
              // 초과분 해제
              const last = nonSeoul.pop();
              const inp = elRegionBox.querySelector(`input[type="checkbox"][value="${cssEscape(last)}"]`);
              if (inp) inp.checked = false;
            }
          }
        } else {
          seoulInput.checked = false;
        }
      });
    }
  }

  function getCheckedRegions() {
    if (!elRegionBox) return [];
    return $$(`#control-region-checkboxes input[type="checkbox"]:checked`).map(x => x.value);
  }

  // CSS.escape polyfill-ish
  function cssEscape(s) {
    return s.replace(/"/g, '\\"');
  }

  // -----------------------------
  // 4) API fetch + cache + Seoul aggregate
  // -----------------------------
  // Elderly endpoint: /api/elderly/forecast/<region>
  // Response:
  // { status:"success", data:{ region, history:[{year,value}], forecast:[{year,value}], message } }

  // Lonely endpoint assumed:
  // /api/lonely/forecast?region=<region>
  // (동일한 data.history / data.forecast 구조라고 가정)
  // 만약 다르면 extractLonelyHistory/Forecast만 바꾸면 됨.

  const cache = {
    elderlyRaw: new Map(), // key: region => json
    lonelyRaw: new Map(),  // key: region => json
    // 서울 집계는 계산 결과 캐시
    elderlySeoul: null, // { history:[], forecast:[] }
    lonelySeoul: null,
  };

  async function fetchJson(url) {
    const res = await fetch(url, { headers: { "Accept": "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${url}`);
    return await res.json();
  }

  async function fetchElderlyRaw(region) {
    if (cache.elderlyRaw.has(region)) return cache.elderlyRaw.get(region);
    const json = await fetchJson(`/api/elderly/forecast/${encodeURIComponent(region)}`);
    cache.elderlyRaw.set(region, json);
    return json;
  }

  async function fetchLonelyRaw(region) {
    if (cache.lonelyRaw.has(region)) return cache.lonelyRaw.get(region);
    const json = await fetchJson(`/api/lonely/forecast?region=${encodeURIComponent(region)}`);
    cache.lonelyRaw.set(region, json);
    return json;
  }

  function extractHistory(json) {
    return (json?.data?.history || []).map(p => ({ year: Number(p.year), value: Number(p.value) || 0 }));
  }

  function extractForecast(json) {
    return (json?.data?.forecast || []).map(p => ({ year: Number(p.year), value: Number(p.value) || 0 }));
  }

  function sumSeriesByYear(seriesList) {
    const map = new Map(); // year -> sum
    for (const series of seriesList) {
      for (const p of series) {
        const y = Number(p.year);
        const v = Number(p.value) || 0;
        map.set(y, (map.get(y) || 0) + v);
      }
    }
    return Array.from(map.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([year, value]) => ({ year, value }));
  }

  async function buildSeoulAgg(fetchRawFn) {
    // 25개 구 전체 fetch → history/forecast 각각 합산
    const jsonList = await Promise.all(GU_LIST.map(r => fetchRawFn(r)));
    const histList = jsonList.map(extractHistory);
    const foreList = jsonList.map(extractForecast);
    return {
      history: sumSeriesByYear(histList),
      forecast: sumSeriesByYear(foreList),
    };
  }

  async function getElderlySeries(region) {
    if (region === SEOUL_LABEL) {
      if (!cache.elderlySeoul) cache.elderlySeoul = await buildSeoulAgg(fetchElderlyRaw);
      return cache.elderlySeoul;
    }
    const raw = await fetchElderlyRaw(region);
    return { history: extractHistory(raw), forecast: extractForecast(raw) };
  }

  async function getLonelySeries(region) {
    if (region === SEOUL_LABEL) {
      if (!cache.lonelySeoul) cache.lonelySeoul = await buildSeoulAgg(fetchLonelyRaw);
      return cache.lonelySeoul;
    }
    const raw = await fetchLonelyRaw(region);
    return { history: extractHistory(raw), forecast: extractForecast(raw) };
  }

  // -----------------------------
  // 5) Chart rendering (Chart.js)
  // -----------------------------
  const charts = new Map(); // canvasId -> Chart instance

  function getCssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function setCanvasLoading(canvasId, isLoading) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    const wrap = el.closest(".chart-wrapper");
    if (!wrap) return;
    wrap.dataset.loading = isLoading ? "true" : "false";
    wrap.style.opacity = isLoading ? "0.55" : "1";
    wrap.style.pointerEvents = isLoading ? "none" : "auto";
  }

  function destroyChart(canvasId) {
    const c = charts.get(canvasId);
    if (c) {
      c.destroy();
      charts.delete(canvasId);
    }
  }

  function renderLineChart(canvasId, title, points, opts = {}) {
    const el = document.getElementById(canvasId);
    if (!el || !window.Chart) return;

    const primary = getCssVar("--color-primary", "#2563eb");
    const textSub = getCssVar("--color-text-sub", "rgba(15,23,42,0.68)");
    const border = getCssVar("--color-border", "rgba(15,23,42,0.14)");

    const labels = points.map(p => String(p.year));
    const data = points.map(p => Number(p.value));

    destroyChart(canvasId);

    const ctx = el.getContext("2d");
    const chart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: title,
          data,
          tension: 0.25,
          fill: false,
          borderWidth: 2,
          borderColor: primary,
          pointRadius: 1.5,
          pointHoverRadius: 3,
          ...(opts.dashed ? { borderDash: [6, 4] } : {}),
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
        },
        scales: {
          x: {
            grid: { color: border },
            ticks: { color: textSub },
          },
          y: {
            grid: { color: border },
            ticks: { color: textSub },
          }
        }
      }
    });

    charts.set(canvasId, chart);
  }

  // -----------------------------
  // 6) Apply + render
  // -----------------------------
  function getStateFromUi(prev) {
    const ys = elYearStart ? Number(elYearStart.value) : prev.ys;
    const ye = elYearEnd ? Number(elYearEnd.value) : prev.ye;

    let regions = getCheckedRegions();
    // fallback: if none checked, use previous or default
    if (regions.length === 0) regions = prev.regions.length ? prev.regions : DEFAULT_STATE.regions.slice();

    // max 2 sanitize
    regions = regions.slice(0, 2);

    // if toggle is ON but seoul not in list, force it
    if (elToggleSeoul?.checked && !regions.includes(SEOUL_LABEL)) {
      // keep at most 1 other
      const other = regions.filter(x => x !== SEOUL_LABEL).slice(0, 1);
      regions = [SEOUL_LABEL, ...other].slice(0, 2);
      // reflect in UI checkboxes
      syncRegionChecks(regions);
    }

    return { ys, ye, regions, includeSeoul: regions.includes(SEOUL_LABEL) };
  }

  function syncRegionChecks(regions) {
    if (!elRegionBox) return;
    $$(`#control-region-checkboxes input[type="checkbox"]`).forEach(inp => {
      inp.checked = regions.includes(inp.value);
    });
    if (elToggleSeoul) elToggleSeoul.checked = regions.includes(SEOUL_LABEL);
  }

  function filterHistoryByYear(history, ys, ye) {
    return history.filter(p => p.year >= ys && p.year <= ye);
  }

  async function renderSlot(slotIndex, region, ys, ye) {
    // slotIndex 1 or 2
    const isSlot2 = slotIndex === 2;

    const titleEl = isSlot2 ? elTitle2 : elTitle1;
    if (titleEl) titleEl.textContent = region;

    const ids = isSlot2 ? CANVAS.s2 : CANVAS.s1;

    // show loading
    setCanvasLoading(ids.trendE, true);
    setCanvasLoading(ids.trendL, true);
    setCanvasLoading(ids.foreE, true);
    setCanvasLoading(ids.foreL, true);

    try {
      const [elderly, lonely] = await Promise.all([
        getElderlySeries(region),
        getLonelySeries(region),
      ]);

      const histE = filterHistoryByYear(elderly.history, ys, ye);
      const histL = filterHistoryByYear(lonely.history, ys, ye);

      // forecast는 5년 예측 그대로 표시(연도범위와 별개)
      const foreE = elderly.forecast;
      const foreL = lonely.forecast;

      renderLineChart(ids.trendE, "독거노인 추세", histE, { dashed: false });
      renderLineChart(ids.trendL, "고독사 추세", histL, { dashed: false });
      renderLineChart(ids.foreE, "독거노인 5년 예측", foreE, { dashed: true });
      renderLineChart(ids.foreL, "고독사 5년 예측", foreL, { dashed: true });

    } catch (e) {
      console.error("[dashboard] renderSlot error:", e);
      // 빈 차트 대신 destroy
      destroyChart(ids.trendE);
      destroyChart(ids.trendL);
      destroyChart(ids.foreE);
      destroyChart(ids.foreL);
    } finally {
      setCanvasLoading(ids.trendE, false);
      setCanvasLoading(ids.trendL, false);
      setCanvasLoading(ids.foreE, false);
      setCanvasLoading(ids.foreL, false);
    }
  }

  async function renderAll(state) {
    // slot 1 always
    const r1 = state.regions[0] || DEFAULT_STATE.regions[0];
    const r2 = state.regions[1] || null;

    await renderSlot(1, r1, state.ys, state.ye);

    if (r2) {
      if (elCol2) elCol2.style.display = "";
      await renderSlot(2, r2, state.ys, state.ye);
    } else {
      // slot2 숨김
      if (elCol2) elCol2.style.display = "none";
      // 기존 차트 파괴
      destroyChart(CANVAS.s2.trendE);
      destroyChart(CANVAS.s2.trendL);
      destroyChart(CANVAS.s2.foreE);
      destroyChart(CANVAS.s2.foreL);
    }
  }

  // -----------------------------
  // 7) Boot
  // -----------------------------
  async function main() {
    // 1) initial state
    let state = parseStateFromUrl();
    async function resolveDefaultYearRange(state) {
      // URL에 ys/ye가 명시되어 있으면 그대로 사용
      const sp = new URLSearchParams(window.location.search);
      const hasYs = sp.has("ys");
      const hasYe = sp.has("ye");
      if (hasYs && hasYe) return state;

      try {
        // 기본 지역 하나로 history를 가져와서 최근 연도 자동 계산
        // (서울시 전체를 켠 경우 서울 집계는 비용이 크니까 기본 구로 먼저 잡자)
        const baseRegion = (state.regions && state.regions.length)
          ? state.regions.find(r => r !== "서울시 전체") || "강남구"
          : "강남구";

        const raw = await fetchElderlyRaw(baseRegion); // 기존 함수 사용
        const hist = extractHistory(raw);              // [{year,value}...]

        if (hist.length) {
          const years = hist.map(p => p.year).filter(Number.isFinite);
          const minY = Math.min(...years);
          const maxY = Math.max(...years);

          // 최근 7년 기본 (데이터가 7년 미만이면 min~max)
          const ye = maxY;
          const ys = Math.max(minY, maxY - 6);

          return { ...state, ys, ye };
        }
      } catch (e) {
        // ignore: 아래 fallback으로 감
      }

      // fallback
      return { ...state, ys: 2017, ye: 2023 };
    }
    state = await resolveDefaultYearRange(state);
    // 2) init UI
    initYearSelects(state);
    renderRegionChips(state);
    syncRegionChecks(state.regions);

    // 3) apply button
    if (elApplyBtn) {
      elApplyBtn.addEventListener("click", async () => {
        const next = getStateFromUi(state);
        writeStateToUrl(next);
        await renderAll(next);
      });
    }

    // 4) initial render
    // URL에 아무것도 없고 체크도 없으면 default를 체크로 반영
    if (!getCheckedRegions().length) {
      syncRegionChecks(state.regions);
    }
    await renderAll(state);
  }

  // DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    main().catch(err => console.error("[dashboard] init error:", err));
  });

})();
