// static/js/ai_page.js
// ChatGPT-Style Logic (Fixed JSON Parsing & Added Guide)

$(document).ready(function () {
  // State
  let currentMode = "translate";
  const modeLabels = {
    translate: "AI 번역",
    sentiment: "감정 분석",
    entities: "개체 분석",
    summary: "텍스트 요약",
    qa: "질의 응답",
    guide: "사용 가이드"
  };

  // DOM Elements
  const $sidebar = $("#ai-sidebar");
  const $chatContainer = $("#ai-chat-container");
  const $chatBox = $("#ai-chat-box");
  const $welcome = $("#ai-welcome");

  const $input = $("#ai-input-text");
  const $sendBtn = $("#ai-run-btn");
  const $plusBtn = $("#btn-toggle-options");
  const $optionsMenu = $("#ai-options-menu");

  // Options
  const $optTranslate = $("#opt-translate");
  const $optQa = $("#opt-qa");
  const $transDir = $("#opt-trans-direction");
  const $qaContext = $("#opt-qa-context");

  // 1. Mode Switching
  $(".ai-nav-btn[data-mode]").on("click", function () {
    const mode = $(this).data("mode");

    // Special Case: Guide
    if (mode === "guide") {
      runGuide();
      return;
    }

    $(".ai-nav-btn").removeClass("active");
    $(this).addClass("active");

    currentMode = mode;
    $("#current-mode-label").text(modeLabels[currentMode]);

    // Update Options Visibility
    $optTranslate.hide();
    $optQa.hide();

    if (currentMode === "translate") $optTranslate.show();
    if (currentMode === "qa") $optQa.show();

    // Auto-focus input
    $input.focus();
  });

  // 2. Options Toggle
  $plusBtn.on("click", function () {
    $(this).toggleClass("open");
    $optionsMenu.toggleClass("show");
  });

  $(document).on("click", function (e) {
    if (!$(e.target).closest(".ai-input-wrapper").length) {
      $plusBtn.removeClass("open");
      $optionsMenu.removeClass("show");
    }
  });

  // 3. Auto-grow Textarea
  $input.on("input", function () {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
    if (this.value === "") this.style.height = "auto";
  });

  $input.on("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      runAI();
    }
  });

  // 4. Send Logic
  $sendBtn.on("click", runAI);

  function runAI() {
    const text = $input.val().trim();
    if (!text) return;

    $welcome.hide();
    $input.val("").css("height", "auto");

    addBubble("user", escapeHtml(text));
    setLoading(true);

    const payload = { text: text, options: {} };
    if (currentMode === "translate") payload.options.direction = $transDir.val();
    if (currentMode === "qa") payload.options.context = $qaContext.val();

    const token = getToken();
    const endpoint = `/api/ai/${currentMode}`;

    if (!token) {
      addBubble("assistant", "로그인이 필요합니다.");
      setLoading(false);
      return;
    }

    $.ajax({
      url: endpoint,
      method: "POST",
      contentType: "application/json",
      headers: { "Authorization": "Bearer " + token },
      data: JSON.stringify(payload),
      success: function (resp) {
        if ($typingIndicator) { $typingIndicator.remove(); $typingIndicator = null; }

        let content = "결과를 가져올 수 없습니다.";
        if (resp.result) {
          content = humanizeResponse(currentMode, resp.result);
        } else if (resp.message) {
          content = resp.message;
        }
        addBubble("assistant", content);
      },
      error: function (xhr) {
        if ($typingIndicator) { $typingIndicator.remove(); $typingIndicator = null; }
        addBubble("assistant", "오류가 발생했습니다. (서버 연결 실패)");
      },
      complete: function () {
        setLoading(false);
      }
    });
  }

  // 5. Humanizer (Robust JSON -> Natural Text)
  function humanizeResponse(mode, result) {
    try {
      if (typeof result === "string") return formatMarkdown(result);

      // Sentiment: { label: "1"/"0", score: ... }
      if (mode === "sentiment") {
        const data = Array.isArray(result) ? result[0] : result;
        if (!data || (!data.label && data.label !== 0)) return formatMarkdown(JSON.stringify(result, null, 2));

        const labelMap = { "POSITIVE": "긍정", "NEGATIVE": "부정", "0": "부정", "1": "긍정", "neutral": "중립", "NEUTRAL": "중립" };
        let raw = String(data.label).toUpperCase();
        let label = labelMap[raw] || raw;
        let score = (data.score * 100).toFixed(1);

        let msg = "";
        if (label === "긍정") msg = `이 문장은 **${score}%**의 확률로 **긍정적**인 내용을 담고 있네요! 😄`;
        else if (label === "부정") msg = `음, 이 문장은 **${score}%**의 확률로 **부정적**인 감정이 느껴집니다. 😟`;
        else msg = `이 문장의 감정은 **${label}** (${score}%)로 분석됩니다.`;

        return formatMarkdown(msg);
      }

      // Entities: { entities: [...] } logic
      if (mode === "entities") {
        let list = result.entities ? result.entities : result;
        if (!Array.isArray(list)) return formatMarkdown(JSON.stringify(result, null, 2));

        if (list.length === 0) return "이 문장에서는 특별한 인물이나 장소 같은 개체명을 찾지 못했습니다.";

        let msg = "문장에서 다음과 같은 주요 키워드를 발견했습니다:\n\n";
        list.forEach(item => {
          let type = item.entity_group || item.entity || "Unknown";
          msg += `- **${item.text}** (${type})\n`;
        });
        return formatMarkdown(msg);
      }

      // Translate: { translation: "..." }
      if (mode === "translate") {
        if (result.translation) return formatMarkdown(result.translation);
        if (result.translation_text) return formatMarkdown(result.translation_text);
      }

      // Summary: { summary: "..." }
      if (mode === "summary") {
        if (result.summary) return formatMarkdown(`**[요약 결과]**\n\n${result.summary}`);
        if (result.summary_text) return formatMarkdown(`**[요약 결과]**\n\n${result.summary_text}`);
      }

      // QA: { answer: "..." }
      if (mode === "qa") {
        if (!result.answer) return "질문에 대한 적절한 답변을 찾지 못했습니다. 본문(Context) 내용을 다시 확인해 주세요.";
        return formatMarkdown(`**답변:** ${result.answer}`);
      }

      // Fallback
      return formatMarkdown(JSON.stringify(result, null, 2));

    } catch (e) {
      console.error("Humanize Error:", e);
      return formatMarkdown("결과를 표시하는 중 오류가 발생했습니다.\n\n" + JSON.stringify(result));
    }
  }

  // 6. Guide Logic
  function runGuide() {
    $welcome.hide();
    const guideText = `
**[AI 사용 가이드]**

1. **AI 번역**: 한영/영한 번역을 해줍니다. 하단 (+) 버튼을 눌러 방향을 바꿀 수 있습니다.
2. **감정 분석**: 문장에 담긴 감정(긍정/부정)을 분석해줍니다.
3. **개체 분석**: 문장에서 인물, 장소, 기관 등 핵심 키워드를 찾아줍니다.
4. **텍스트 요약**: 긴 글을 짧게 요약해줍니다.
5. **질의 응답**: (+) 버튼을 눌러 **'지문(Context)'**에 긴 글을 넣고, 채팅창에 질문하면 그 글을 바탕으로 대답해줍니다.

왼쪽 메뉴에서 기능을 선택하고 대화를 시작해 보세요!
    `;
    addBubble("assistant", formatMarkdown(guideText));
  }

  // Helpers
  function getToken() { return localStorage.getItem("access_token") || ""; }

  let $typingIndicator = null;
  function setLoading(isLoading) {
    $sendBtn.prop("disabled", isLoading);
    if (isLoading) showTyping();
    else {
      if ($typingIndicator) { $typingIndicator.remove(); $typingIndicator = null; }
      $input.focus();
    }
  }

  function showTyping() {
    const tmpl = `<div class="d-flex align-items-center gap-1" style="height:24px;">
      <span class="typing-dot" style="animation-delay:0s">●</span>
      <span class="typing-dot" style="animation-delay:0.2s">●</span>
      <span class="typing-dot" style="animation-delay:0.4s">●</span>
    </div>`;
    $typingIndicator = addRawBubble("assistant", tmpl);
  }

  function addBubble(role, text) {
    let html = (role === "user") ? `<div style="white-space:pre-wrap;">${text}</div>` : text;
    addRawBubble(role, html);
  }

  function addRawBubble(role, htmlContent) {
    const bubbleClass = role === "user" ? "ai-user" : "ai-assistant";
    const $el = $(`<div class="ai-bubble ${bubbleClass}"></div>`).html(htmlContent).hide();
    $chatBox.append($el);
    $el.fadeIn(300);
    document.getElementById("ai-chat-container").scrollTop = 99999;
    return $el;
  }

  function escapeHtml(s) { return $('<div>').text(s).html(); }

  function formatMarkdown(text) {
    let out = text || "";
    out = out.replace(/```(\w+)?\n?([\s\S]*?)```/g, function (match, lang, code) {
      lang = lang || "text";
      return `<div class="ai-code-block"><div class="code-header"><span class="lang">${lang}</span><button class="btn-copy">Copy</button></div><pre><code>${code.trim()}</code></pre><div style="display:none;" class="raw-code">${code.trim()}</div></div>`;
    });
    out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/\n/g, '<br>');
    return out;
  }

  $(document).on("click", ".btn-copy", function () {
    const $btn = $(this);
    const rawCode = $btn.closest(".ai-code-block").find(".raw-code").text();
    navigator.clipboard.writeText(rawCode).then(() => {
      const orig = $btn.text();
      $btn.text("Copied!");
      setTimeout(() => $btn.text(orig), 2000);
    });
  });

  $("#btn-clear-chat").on("click", function () {
    $chatBox.empty();
    $welcome.show();
  });
  // 7. Sidebar Toggle Logic (Mobile)
  const $overlay = $("#ai-sidebar-overlay");
  const $toggleBtn = $("#btn-toggle-sidebar");

  function toggleSidebar() {
    $sidebar.toggleClass("open");
    $overlay.toggleClass("show");
  }

  function closeSidebar() {
    $sidebar.removeClass("open");
    $overlay.removeClass("show");
  }

  $toggleBtn.on("click", function (e) {
    e.stopPropagation();
    toggleSidebar();
  });

  $overlay.on("click", function () {
    closeSidebar();
  });

  // Close sidebar when clicking a nav item on mobile
  $(".ai-nav-btn").on("click", function () {
    if ($(window).width() <= 768) {
      closeSidebar();
    }
  });

  // Handle Resize
  $(window).on("resize", function () {
    if ($(window).width() > 768) {
      closeSidebar(); // Reset mobile state when expanding
    }
  });
});

