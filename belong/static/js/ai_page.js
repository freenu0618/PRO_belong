// static/js/ai_page.js
document.addEventListener("DOMContentLoaded", () => {
  const serviceSelect = document.getElementById("ai-service-select");
  const inputEl = document.getElementById("ai-input-text");
  const chatBox = document.getElementById("ai-chat-box");
  const runBtn = document.getElementById("ai-run-btn");
  const clearBtn = document.getElementById("ai-clear-btn");

  const directionEl = document.getElementById("ai-translate-direction");
  const translateOpts = document.getElementById("translate-options");

  const qaOpts = document.getElementById("qa-options");
  const qaContextEl = document.getElementById("ai-qa-context");

  const serviceHelp = document.getElementById("ai-service-help");

  if (!serviceSelect || !inputEl || !chatBox || !runBtn) return;

  const helpTexts = {
    translate: "번역: 한↔영 번역(방향 선택)",
    sentiment: "감정 분석: 문장의 감정(긍정/부정 등)을 분석",
    entities: "개체 분석: 텍스트에서 사람/장소/기관 등 엔티티를 추출",
    summary: "요약: 핵심만 짧게 요약",
    qa: "질의응답(QA): 질문 + 컨텍스트(문서)를 기반으로 답변",
  };

  const endpointMap = {
    translate: "/api/ai/translate",
    sentiment: "/api/ai/sentiment",
    entities: "/api/ai/entities",
    summary: "/api/ai/summary",
    qa: "/api/ai/qa",
  };

  function getToken() {
    return window.BelongAuth?.getToken?.() || localStorage.getItem("access_token") || "";
  }

  function setLoading(isLoading) {
    runBtn.disabled = isLoading;
    runBtn.textContent = isLoading ? "처리중..." : "실행";
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function addBubble(role, html) {
    const wrap = document.createElement("div");
    wrap.className = `ai-bubble ai-${role}`;
    wrap.style.marginBottom = "10px";
    wrap.innerHTML = html;
    chatBox.appendChild(wrap);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function addText(role, text) {
    addBubble(role, `<div><strong>${role === "user" ? "나" : "AI"}</strong></div>
      <div style="white-space:pre-wrap;">${escapeHtml(text)}</div>`);
  }

  function addJson(role, obj) {
    const pretty = JSON.stringify(obj, null, 2);
    addBubble(role, `<div><strong>${role === "user" ? "나" : "AI"}</strong></div>
      <pre class="mb-0 mt-1 p-2 border rounded-2" style="background:#fff; white-space:pre-wrap;">${escapeHtml(pretty)}</pre>`);
  }

  function setHelp() {
    const svc = serviceSelect.value;
    if (serviceHelp) serviceHelp.textContent = helpTexts[svc] || "";
  }

  function toggleOptions() {
    const svc = serviceSelect.value;
    if (translateOpts) translateOpts.style.display = svc === "translate" ? "block" : "none";
    if (qaOpts) qaOpts.style.display = svc === "qa" ? "block" : "none";
    setHelp();
  }

  async function callApi(service, payload) {
    const url = endpointMap[service];
    if (!url) throw new Error(`Unknown service: ${service}`);

    const token = getToken();
    if (!token) {
      // AI는 로그인 필요(서버가 jwt_required로 막는 구조) :contentReference[oaicite:10]{index=10}
      throw new Error("로그인이 필요합니다. 먼저 로그인해주세요.");
    }

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    // 401이면 토큰 만료/미로그인
    if (res.status === 401) {
      // auth_ui.js도 만료 토큰이면 지우는 정책 :contentReference[oaicite:11]{index=11}
      window.BelongAuth?.clearToken?.();
      throw new Error("인증이 만료되었거나 로그인되지 않았습니다. 다시 로그인해주세요.");
    }

    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = json?.message || json?.error || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return json;
  }

  function buildPayload() {
    const svc = serviceSelect.value;
    const text = (inputEl.value || "").trim();

    if (!text) throw new Error("텍스트(또는 질문)를 입력해주세요.");

    // AI 라우트가 기대하는 공통 포맷: { text, options } :contentReference[oaicite:12]{index=12}
    const payload = { text, options: {} };

    if (svc === "translate") {
      payload.options.direction = (directionEl?.value || "ko-en").trim();
    }

    if (svc === "qa") {
      const ctx = (qaContextEl?.value || "").trim();
      if (!ctx) throw new Error("QA는 컨텍스트(문서/정보)가 필요합니다.");
      payload.options.context = ctx;
    }

    return payload;
  }

  function showLoginCtaIfNeeded() {
    const token = getToken();
    if (token) return;
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    addBubble(
      "assistant",
      `<div><strong>AI</strong></div>
       <div class="mt-1">
         AI 기능은 로그인이 필요합니다.
         <a class="ms-2" href="/login?next=${next}">로그인 하러가기</a>
       </div>`
    );
  }

  serviceSelect.addEventListener("change", toggleOptions);

  clearBtn?.addEventListener("click", () => {
    inputEl.value = "";
    if (qaContextEl) qaContextEl.value = "";
    chatBox.innerHTML = "";
    toggleOptions();
    showLoginCtaIfNeeded();
  });

  runBtn.addEventListener("click", async () => {
    try {
      setLoading(true);
      const svc = serviceSelect.value;

      const payload = buildPayload();
      addText("user", payload.text);

      const json = await callApi(svc, payload);

      // ai_route.py 공통 응답은 { ok, result } :contentReference[oaicite:13]{index=13}
      if (json?.ok === false) {
        addJson("assistant", json);
        return;
      }
      addJson("assistant", json?.result ?? json);
    } catch (err) {
      console.error(err);
      addText("assistant", err?.message || "오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  });

  // 초기 상태
  toggleOptions();
  showLoginCtaIfNeeded();
});
