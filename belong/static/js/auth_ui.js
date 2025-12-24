// static/js/auth_ui.js
(() => {
  "use strict";

  const TOKEN_KEY = "access_token";

  function normalizeToken(t) {
    if (!t) return null;
    t = String(t).trim();

    // "...." 또는 '....' 형태면 따옴표 제거
    if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
      t = t.slice(1, -1).trim();
    }

    return t || null;
  }

  function getToken() {
    // localStorage 우선, 없으면 sessionStorage
    const t1 = normalizeToken(localStorage.getItem(TOKEN_KEY));
    if (t1) return t1;
    const t2 = normalizeToken(sessionStorage.getItem(TOKEN_KEY));
    if (t2) return t2;
    return null;
  }

  function setToken(token, remember = true) {
    const t = normalizeToken(token);
    if (!t) return;

    if (remember) {
      localStorage.setItem(TOKEN_KEY, t);
      sessionStorage.removeItem(TOKEN_KEY);
    } else {
      sessionStorage.setItem(TOKEN_KEY, t);
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
  }

  async function apiMe() {
    const token = getToken();

    // ✅ 토큰 없으면 me 호출 자체를 하지 않음 (지금 에러의 직접 원인 차단)
    if (!token) return { ok: false, status: "no-token", user: null };

    const res = await fetch("/api/auth/me", {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json",
      },
    });

    const json = await res.json().catch(() => null);

    if (!res.ok) {
      // 401이면 토큰 문제일 가능성이 높음
      return { ok: false, status: `http-${res.status}`, user: null, json };
    }

    // ✅ 수정: json.ok === true 확인 (API 응답 형식에 맞춤)
    if (!json || json.ok !== true) {
      return { ok: false, status: "bad-payload", user: null, json };
    }

    return { ok: true, status: "ok", user: json.data?.user ?? null };
  }


  // ---- UI 토글 (너 프로젝트 네비 id 기준) ----
  function setNavLoggedOut() {
    const navLogin = document.getElementById("nav-login");
    const navSignup = document.getElementById("nav-signup");
    const navUser = document.getElementById("nav-user");

    if (navLogin) navLogin.classList.remove("d-none");
    if (navSignup) navSignup.classList.remove("d-none");
    if (navUser) navUser.classList.add("d-none");
  }

  function setNavLoggedIn(user) {
    const navLogin = document.getElementById("nav-login");
    const navSignup = document.getElementById("nav-signup");
    const navUser = document.getElementById("nav-user");
    const navUsername = document.getElementById("nav-username");

    if (navLogin) navLogin.classList.add("d-none");
    if (navSignup) navSignup.classList.add("d-none");
    if (navUser) navUser.classList.remove("d-none");
    if (navUsername) navUsername.textContent = user?.username ?? "사용자";
  }

  async function logout() {
    const token = getToken();
    try {
      if (token) {
        await fetch("/api/auth/logout", {
          method: "POST",
          headers: { "Authorization": `Bearer ${token}` },
        }).catch(() => { });
      }
    } finally {
      clearToken();
      setNavLoggedOut();
      window.location.href = "/";
    }
  }

  async function boot() {
    // 로그아웃 버튼 연결
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logout();
    });

    // ✅ 토큰 없으면: 그냥 로그아웃 UI로 끝
    const token = getToken();
    if (!token) {
      setNavLoggedOut();
      return;
    }

    // 토큰 있으면 /me로 검증
    const result = await apiMe();

    if (!result.ok) {
      // 401이면 토큰 만료/불일치 가능 → 토큰 제거
      if (result.status === "http-401") {
        clearToken();
      }
      setNavLoggedOut();
      return;
    }

    setNavLoggedIn(result.user);
  }

  // 로그인/회원가입 페이지에서 쓸 수 있게 노출
  window.BelongAuth = { getToken, setToken, clearToken };

  document.addEventListener("DOMContentLoaded", boot);
})();
