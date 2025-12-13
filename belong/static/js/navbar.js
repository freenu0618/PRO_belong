// static/js/navbar.js
document.addEventListener("DOMContentLoaded", () => {
  const navLogin = document.getElementById("nav-login");
  const navSignup = document.getElementById("nav-signup");
  const navUser = document.getElementById("nav-user");
  const navUsername = document.getElementById("nav-username");
  const logoutBtn = document.getElementById("logout-btn");

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

  // 2) Login state (P2에서 JWT 정식 연결 예정)
  //    지금 단계(P0)에서는: access_token(또는 belong_user) 존재 여부로만 UI 토글.
  const token =
    localStorage.getItem("access_token") ||
    localStorage.getItem("belong_access_token") ||
    "";

  let user = null;
  try {
    user = JSON.parse(localStorage.getItem("belong_user") || "null");
  } catch (e) {
    user = null;
  }

  const isLoggedIn = Boolean(token) || Boolean(user && user.username);

  if (isLoggedIn) {
    navLogin?.classList.add("d-none");
    navSignup?.classList.add("d-none");
    navUser?.classList.remove("d-none");
    if (navUsername) navUsername.textContent = (user && user.username) ? user.username : "사용자";

    logoutBtn?.addEventListener("click", () => {
      localStorage.removeItem("belong_user");
      localStorage.removeItem("access_token");
      localStorage.removeItem("belong_access_token");
    });
  } else {
    navLogin?.classList.remove("d-none");
    navSignup?.classList.remove("d-none");
    navUser?.classList.add("d-none");
  }
});
