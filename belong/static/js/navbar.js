// static/js/navbar.js
// 네비게이션 바 UI 로직 (인증은 auth_ui.js에서 처리)
document.addEventListener("DOMContentLoaded", () => {
  // 1) Active state (underline) — 현재 URL 기준으로 nav-link에 .active 부여
  try {
    const path = window.location.pathname.replace(/\/+$/, "") || "/";
    const links = document.querySelectorAll('[data-component="navbar"] a.nav-link[href]');
    links.forEach((a) => {
      const hrefRaw = a.getAttribute("href") || "";
      if (!hrefRaw.startsWith("/")) return; // 외부/해시 링크 제외
      const href = hrefRaw.replace(/\/+$/, "") || "/";
      const isActive = href === "/" ? path === "/" : path.startsWith(href);
      if (isActive) {
        a.classList.add("active");
        a.setAttribute("aria-current", "page");
      }
    });
  } catch (e) {
    // ignore
  }

  // ✅ 인증 로직 제거 - auth_ui.js에서 처리
  // navbar.js는 링크 활성화만 담당
});
