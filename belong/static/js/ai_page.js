// static/js/ai_page.js
// jQuery Version

$(document).ready(function () {
  const $serviceSelect = $("#ai-service-select");
  const $inputEl = $("#ai-input-text");
  const $chatBox = $("#ai-chat-box");
  const $runBtn = $("#ai-run-btn");
  const $clearBtn = $("#ai-clear-btn");

  const $directionEl = $("#ai-translate-direction");
  const $translateOpts = $("#translate-options");
  const $qaOpts = $("#qa-options");
  const $qaContextEl = $("#ai-qa-context");
  const $serviceHelp = $("#ai-service-help");

  // Quick Select Buttons
  $(".ai-quick-select").on("click", function () {
    const svc = $(this).data("ai-service");
    $serviceSelect.val(svc).trigger("change");
    // Scroll to console
    $("html, body").animate({
      scrollTop: $("#ai-console").offset().top - 100
    }, 500);
  });

  const helpTexts = {
    translate: "번역: 한↔영 번역(방향 선택)",
    sentiment: "감정 분석: 문장의 감정(긍정/부정 등)을 분석",
    entities: "개체 분석: 텍스트에서 사람/장소/기관 등 엔티티를 추출",
    summary: "요약: 핵심만 짧게 요약",
    qa: "질의응답(QA): 질문 + 지문(Context)을 기반으로 답변",
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
    $runBtn.prop("disabled", isLoading);
    $runBtn.text(isLoading ? "처리중..." : "실행");
  }

  function escapeHtml(s) {
    if (typeof s !== "string") s = String(s);
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function addBubble(role, htmlContent) {
    // role: 'user' | 'assistant'
    const bubbleClass = role === "user" ? "ai-user" : "ai-assistant";
    const $wrap = $(`<div class="ai-bubble ${bubbleClass}"></div>`).html(htmlContent).hide();

    $chatBox.append($wrap);
    $wrap.fadeIn(300);

    // Scroll to bottom
    $chatBox.scrollTop($chatBox[0].scrollHeight);
  }

  function addTextBubble(role, text) {
    const label = role === "user" ? "나" : "AI";
    const safeText = escapeHtml(text);
    const html = `
      <div class="fw-bold mb-1" style="font-size:0.8rem; opacity:0.8;">${label}</div>
      <div style="white-space:pre-wrap;">${safeText}</div>
    `;
    addBubble(role, html);
  }

  function addJsonBubble(role, obj) {
    const label = role === "user" ? "나" : "AI";
    const pretty = JSON.stringify(obj, null, 2);
    const html = `
      <div class="fw-bold mb-1" style="font-size:0.8rem; opacity:0.8;">${label}</div>
      <pre>${escapeHtml(pretty)}</pre>
    `;
    addBubble(role, html);
  }

  function updateOptions() {
    const svc = $serviceSelect.val();

    // Help text
    $serviceHelp.text(helpTexts[svc] || "");

    // Toggle specific options with slide effect
    if (svc === "translate") {
      $translateOpts.slideDown(200);
    } else {
      $translateOpts.slideUp(200);
    }

    if (svc === "qa") {
      $qaOpts.slideDown(200);
    } else {
      $qaOpts.slideUp(200);
    }
  }

  $serviceSelect.on("change", updateOptions);

  $clearBtn.on("click", function () {
    $inputEl.val("");
    $qaContextEl.val("");
    $chatBox.empty().append('<div class="text-muted small">초기화되었습니다.</div>');
    updateOptions();
  });

  $runBtn.on("click", function () {
    const svc = $serviceSelect.val();
    const text = $inputEl.val().trim();

    if (!text) {
      alert("텍스트를 입력해주세요.");
      $inputEl.focus();
      return;
    }

    setLoading(true);

    // Build Payload
    const payload = { text: text, options: {} };

    if (svc === "translate") {
      payload.options.direction = $directionEl.val();
    }
    if (svc === "qa") {
      const ctx = $qaContextEl.val().trim();
      if (!ctx) {
        alert("지문(Context)을 입력해주세요.");
        $qaContextEl.focus();
        setLoading(false);
        return;
      }
      payload.options.context = ctx;
    }

    // Add User Bubble
    addTextBubble("user", text);

    // AJAX Call
    const token = getToken();
    if (!token) {
      addBubble("assistant", `
        <div>
          <strong>로그인 필요</strong><br>
          AI 기능을 사용하려면 로그인이 필요합니다. 
          <a href="/login" class="text-decoration-underline text-warning">로그인 하기</a>
        </div>
      `);
      setLoading(false);
      return;
    }

    $.ajax({
      url: endpointMap[svc],
      method: "POST",
      contentType: "application/json",
      headers: { "Authorization": "Bearer " + token },
      data: JSON.stringify(payload),
      success: function (resp) {
        if (resp.ok === false) {
          addJsonBubble("assistant", resp);
        } else {
          // 성공 시 result만 보여주거나 전체 보여주기
          const result = resp.result !== undefined ? resp.result : resp;

          if (typeof result === "object") {
            addJsonBubble("assistant", result);
          } else {
            addTextBubble("assistant", result);
          }
        }
      },
      error: function (xhr, status, err) {
        if (xhr.status === 401) {
          addBubble("assistant", "<div>인증이 만료되었습니다. 다시 로그인해주세요.</div>");
          window.BelongAuth?.clearToken?.();
        } else {
          let msg = "오류가 발생했습니다.";
          try {
            const json = JSON.parse(xhr.responseText);
            if (json.message) msg = json.message;
            else if (json.error) msg = json.error;
          } catch (e) { }
          addTextBubble("assistant", msg);
        }
      },
      complete: function () {
        setLoading(false);
      }
    });

  });

  // Init
  updateOptions();
});
