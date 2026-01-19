// static/js/app_ui.js
document.addEventListener("DOMContentLoaded", () => {
  const modalEl = document.getElementById("comingSoonModal");
  if (!modalEl || !window.bootstrap) return;

  const titleEl = document.getElementById("comingSoonTitle");
  const bodyEl  = document.getElementById("comingSoonBody");

  const modal = new bootstrap.Modal(modalEl);

  const COPY = {
    agent: {
      title: "AI Agent (준비중)",
      body: "AI Agent는 목표를 받으면 작업을 분해하고 도구를 호출해 결과를 만들어내는 기능입니다. 현재는 UI 구조만 준비해두었고 다음 단계에서 연결됩니다."
    },
    agentic: {
      title: "Agentic AI (준비중)",
      body: "Agentic AI는 멀티 에이전트/워크플로우 기반으로 장기 목표를 수행하는 기능입니다. 현재는 UI 구조만 준비해두었고 다음 단계에서 연결됩니다."
    }
  };

  // data-coming-soon 속성이 붙은 모든 요소가 대상
  document.querySelectorAll("[data-coming-soon]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const key = el.getAttribute("data-coming-soon");
      const copy = COPY[key] || { title: "준비중", body: "현재 준비 중인 기능입니다." };

      if (titleEl) titleEl.textContent = copy.title;
      if (bodyEl) bodyEl.textContent = copy.body;

      modal.show();
    });
  });
});
