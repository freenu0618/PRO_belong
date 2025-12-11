// static/js/ai_page.js
document.addEventListener("DOMContentLoaded", () => {
  const inputEl      = document.getElementById("ai-input-text");
  const chatBoxEl    = document.getElementById("ai-chat-box");
  const runBtn       = document.getElementById("ai-run-btn");
  const clearBtn     = document.getElementById("ai-clear-btn");
  const serviceSelect= document.getElementById("ai-service-select");
  const serviceHelp  = document.getElementById("ai-service-help");

  if (!inputEl || !chatBoxEl || !runBtn || !serviceSelect) {
    return; // ai_tool이 아닌 페이지에서는 아무것도 하지 않음
  }

  // 서비스별 설명 문구
  const helpTexts = {
    sentiment: "감정 분석: 문장의 감정(긍정/부정 등)을 분석합니다.",
    entities:  "개체 분석: 문장에서 사람, 기관, 장소 등을 추출합니다.",
    qa:        "질의 응답: 주어진 텍스트를 기반으로 질문에 답변합니다.",
  };

  function updateServiceHelp() {
    const key = serviceSelect.value;
    if (serviceHelp) {
      serviceHelp.textContent = helpTexts[key] || "";
    }
  }

  serviceSelect.addEventListener("change", updateServiceHelp);
  updateServiceHelp();

  // 채팅 말풍선 추가 함수
  function appendMessage(role, text) {
    const wrap = document.createElement("div");
    wrap.classList.add("mb-2", "d-flex");
    wrap.classList.add(
      role === "user" ? "justify-content-end" : "justify-content-start"
    );

    const bubble = document.createElement("div");
    bubble.classList.add("px-3", "py-2", "rounded-3", "small");

    if (role === "user") {
      bubble.classList.add("bg-primary", "text-white");
    } else {
      bubble.classList.add("bg-light");
    }

    bubble.textContent = text;
    wrap.appendChild(bubble);
    chatBoxEl.appendChild(wrap);

    // 스크롤 아래로
    chatBoxEl.scrollTop = chatBoxEl.scrollHeight;
  }

  // 실행 버튼 클릭
  runBtn.addEventListener("click", async () => {
    const text = (inputEl.value || "").trim();
    if (!text) {
      appendMessage("assistant", "텍스트를 입력해주세요.");
      return;
    }

    const service = serviceSelect.value;

    // 1) 사용자 메시지 먼저 표시
    appendMessage("user", text);
    inputEl.value = "";

    try {
      const payload = {
        text,
        options: {},   // 필요하면 나중에 context 같은 거 넣기
      };

      const res = await fetch(`/api/ai/${service}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || data.ok === false) {
        const msg = data.error || `요청 실패 (${res.status})`;
        appendMessage("assistant", msg);
        return;
      }

      // 2) 서비스별로 응답 텍스트 만들기
      let assistantText = "";

      if (service === "qa") {
        // QA는 answer 필드를 우선 사용
        if (data.result && typeof data.result === "object") {
          assistantText =
            data.result.answer ||
            JSON.stringify(data.result, null, 2);
        } else {
          assistantText = String(data.result);
        }
      } else {
        // 나머지는 일단 JSON 그대로 보여주기
        if (typeof data.result === "string") {
          assistantText = data.result;
        } else {
          assistantText = JSON.stringify(data.result, null, 2);
        }
      }

      appendMessage("assistant", assistantText);
    } catch (err) {
      console.error(err);
      appendMessage("assistant", "서버와 통신 중 오류가 발생했습니다.");
    }
  });

  // 초기화 버튼
  clearBtn?.addEventListener("click", () => {
    chatBoxEl.innerHTML =
      '<div class="text-muted small">대화 내역이 초기화되었습니다.</div>';
  });
});
