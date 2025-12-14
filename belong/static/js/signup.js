// static/js/signup.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signup-form");
  const errorBox = document.getElementById("signup-error");
  if (!form) return;

  const getNextUrl = () => {
    const p = new URLSearchParams(window.location.search);
    const next = p.get("next");
    if (next && next.startsWith("/")) return next;
    return "/";
  };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = (document.getElementById("username")?.value || "").trim();
    const email = (document.getElementById("email")?.value || "").trim();
    const password = (document.getElementById("password")?.value || "").trim();

    if (errorBox) errorBox.style.display = "none";

    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });

      const json = await res.json().catch(() => ({}));

      if (!res.ok || json?.status !== "success") {
        if (errorBox) {
          errorBox.innerText = json?.message || "회원가입에 실패했습니다.";
          errorBox.style.display = "block";
        }
        return;
      }

      const token = json?.data?.access_token;
      const user = json?.data?.user;

      // 회원가입 성공 시 토큰을 내려주는 버전 기준 :contentReference[oaicite:6]{index=6}
      if (token) {
        if (window.BelongAuth?.setToken) window.BelongAuth.setToken(token);
        else localStorage.setItem("access_token", token);
      }
      if (user) localStorage.setItem("belong_user", JSON.stringify(user));

      window.location.href = getNextUrl();
    } catch (err) {
      console.error(err);
      if (errorBox) {
        errorBox.innerText = "서버와 연결할 수 없습니다.";
        errorBox.style.display = "block";
      }
    }
  });
});
