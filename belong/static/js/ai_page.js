// static/js/ai_page.js
document.addEventListener("DOMContentLoaded", () => {
  const serviceSelect = document.getElementById("ai-service-select");
  const inputEl       = document.getElementById("ai-input-text");
  const chatBox       = document.getElementById("ai-chat-box");
  const runBtn        = document.getElementById("ai-run-btn");
  const clearBtn      = document.getElementById("ai-clear-btn");
  const directionEl   = document.getElementById("ai-translate-direction");
  const translateOpts = document.getElementById("translate-options");
  const serviceHelp   = document.getElementById("ai-service-help");

  if (!serviceSelect || !inputEl || !chatBox || !runBtn) return;

  // ---- 서비스별 설명 문구 ----
  const helpTexts = {
    sentiment: "감정 분석: 문장의 감정(긍정/부정 등)을 분석합니다.",
    entities:  "개체 분석: 문장에서 사람, 기관, 장소 등을 추출합니다.",
    qa:        "질의 응답: 주어진 텍스트를 기반으로 질문에 답변합니다.",
    translate: "번역: 한국어↔영어 번역을 수행합니다.",
    summary:   "문장 요약: 긴 문장을 짧게 요약합니다.",
  };

  function updateServiceHelp() {
    const key = serviceSelect.value;
    if (serviceHelp) {
      serviceHelp.textContent = helpTexts[key] || "";
    }
  }

  // 서비스 바뀔 때 번역 옵션 표시/숨기기 + 설명 업데이트
  serviceSelect.addEventListener("change", () => {
    const svc = serviceSelect.value;

    if (translateOpts) {
      translateOpts.style.display = (svc === "translate") ? "block" : "none";
    }

    updateServiceHelp();
  });

  // 초기 상태 반영
  updateServiceHelp();
  if (translateOpts) {
    translateOpts.style.display =
      serviceSelect.value === "translate" ? "block" : "none";
  }

  // ---- 채팅 말풍선 추가 함수 ----
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
    chatBox.appendChild(wrap);

    // 스크롤 아래로
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // ---- 결과 포맷터: 서비스별로 보기 좋게 변환 ----
  function formatResult(service, result) {
    if (result == null) {
      return "결과가 비어 있습니다.";
    }

    // 1) 감정 분석
    if (service === "sentiment") {
      // 우리가 백엔드에서 보내는 형태: { label, score }
      if (typeof result === "object" && !Array.isArray(result)) {
        const label = result.label || "라벨 미상";
        const score =
          typeof result.score === "number"
            ? (result.score * 100).toFixed(1) + "%"
            : "";
        if (score) {
          return `감정 분석 결과: ${label} (${score})`;
        }
        return `감정 분석 결과: ${label}`;
      }

      // 혹시 배열로 올 경우까지 대비
      if (Array.isArray(result)) {
        if (result.length === 0) return "감정 분석 결과가 없습니다.";
        const lines = result.map((item, idx) => {
          const label =
            item.label || item.class || item.prediction || "라벨 미상";
          const score =
            typeof item.score === "number"
              ? (item.score * 100).toFixed(1) + "%"
              : "";
          const prefix = result.length > 1 ? `${idx + 1}. ` : "- ";
          if (score) {
            return `${prefix}${label} (${score})`;
          }
          return `${prefix}${label}`;
        });
        return "감정 분석 결과:\n" + lines.join("\n");
      }

      return typeof result === "string"
        ? result
        : JSON.stringify(result, null, 2);
    }

    // 2) 개체 분석
    if (service === "entities") {
      let entities = [];

      if (Array.isArray(result)) {
        entities = result;
      } else if (result && Array.isArray(result.entities)) {
        entities = result.entities;
      }

      if (entities.length === 0) {
        return "인식된 개체가 없습니다.";
      }

      function mapEntityType(t) {
        if (!t) return "타입 미상";
        const up = String(t).toUpperCase();
        if (up.includes("PER"))  return "사람(PER)";
        if (up.includes("ORG"))  return "기관/회사(ORG)";
        if (up.includes("LOC"))  return "장소(LOC)";
        if (up.includes("MISC")) return "기타(MISC)";
        return t;
      }

      const lines = entities.map((ent, idx) => {
        const word  = ent.text || ent.word || ent.token || "";
        const type  = mapEntityType(ent.entity || ent.entity_group || ent.label);
        const score = typeof ent.score === "number"
          ? (ent.score * 100).toFixed(1) + "%"
          : "";

        let base = `${idx + 1}. "${word}"`;
        const meta = [];
        if (type)  meta.push(`타입: ${type}`);
        if (score) meta.push(`신뢰도: ${score}`);
        if (meta.length > 0) {
          base += ` (${meta.join(", ")})`;
        }
        return base;
      });

      return "인식된 개체들:\n" + lines.join("\n");
    }

    // 3) 질의응답
    if (service === "qa") {
      if (result && typeof result === "object") {
        if (result.answer) {
          const score =
            typeof result.score === "number"
              ? (result.score * 100).toFixed(1) + "%"
              : null;
          if (score) {
            return `답변: ${result.answer}\n(신뢰도: ${score})`;
          }
          return `답변: ${result.answer}`;
        }
        return JSON.stringify(result, null, 2);
      }
      return typeof result === "string"
        ? result
        : JSON.stringify(result, null, 2);
    }

    // 4) 문장 요약
    if (service === "summary") {
      if (result && typeof result === "object" && result.summary) {
        return `요약:\n${result.summary}`;
      }
      return typeof result === "string"
        ? result
        : JSON.stringify(result, null, 2);
    }

    // 5) 번역
    if (service === "translate") {
      if (result && typeof result === "object" && result.translation) {
        const dir = result.direction === "en-ko" ? "영어 → 한국어" : "한국어 → 영어";
        return `번역(${dir}):\n${result.translation}`;
      }
      return typeof result === "string"
        ? result
        : JSON.stringify(result, null, 2);
    }

    // 기타 서비스 fallback
    if (typeof result === "string") {
      return result;
    }
    return JSON.stringify(result, null, 2);
  }

  // ---- 실행 버튼 클릭 ----
  runBtn.addEventListener("click", async () => {
    const text = (inputEl.value || "").trim();
    if (!text) {
      appendMessage("assistant", "텍스트를 입력해주세요.");
      return;
    }

    const service = serviceSelect.value;

    // 1) 사용자 메시지 채팅창에 추가
    appendMessage("user", text);
    inputEl.value = "";

    // 2) 서비스별 URL & options 구성
    let url = "";
    const options = {};

    if (service === "sentiment") {
      url = "/api/ai/sentiment";
    } else if (service === "entities") {
      url = "/api/ai/entities";
    } else if (service === "qa") {
      url = "/api/ai/qa";
    } else if (service === "summary") {
      url = "/api/ai/summary";
      // 필요하면 나중에 options.max_length 등 추가 가능
    } else if (service === "translate") {
      url = "/api/ai/translate";
      if (directionEl) {
        options.direction = directionEl.value; // "ko-en" or "en-ko"
      }
    } else {
      appendMessage("assistant", `알 수 없는 서비스: ${service}`);
      return;
    }

    const payload = {
      text,
      options,
    };

    try {
      const res = await fetch(url, {
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

      const formatted = formatResult(service, data.result);
      appendMessage("assistant", formatted);
    } catch (err) {
      console.error(err);
      appendMessage("assistant", "서버와 통신 중 오류가 발생했습니다.");
    }
  });

  // ---- 초기화 버튼 ----
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      chatBox.innerHTML =
        '<div class="text-muted small">대화 내역이 초기화되었습니다.</div>';
    });
  }
});
