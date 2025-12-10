// static/js/ai_page.js
document.addEventListener("DOMContentLoaded", () => {
  const inputEl  = document.getElementById("ai-input-text");
  const resultEl = document.getElementById("ai-result");
  const runBtn   = document.getElementById("ai-run-btn");

  if (!inputEl || !resultEl || !runBtn) return;

  runBtn.addEventListener("click", async () => {
    const service = runBtn.dataset.service;  // translate / sentiment / ...
    const text = inputEl.value.trim();

    if (!text) {
      resultEl.textContent = "텍스트를 입력해주세요.";
      return;
    }

    let url = `/api/ai/${service}`;
    let payload = {};

    if (service === "translate") {
      payload = {
        text,
        source_lang: "ko",
        target_lang: "en",
      };
    } else if (service === "qa") {
      payload = {
        question: text,
        context: ""
      };
    } else {
      payload = { text };
    }

    resultEl.textContent = "요청 중...";

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok || data.ok === false) {
        resultEl.textContent = data.error || `요청 실패 (${res.status})`;
        return;
      }

      // 우선은 result만 보여주고, 나중에 서비스별로 예쁘게 포맷
      resultEl.textContent = JSON.stringify(data.result, null, 2);
    } catch (err) {
      console.error(err);
      resultEl.textContent = "오류가 발생했습니다.";
    }
  });
});
