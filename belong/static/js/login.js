// static/js/login.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");
  const errorBox = document.getElementById("login-error");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    errorBox.style.display = "none";

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const json = await res.json();

      if (!res.ok || json.status !== "success") {
        errorBox.innerText =
          json.message || "아이디 또는 비밀번호가 올바르지 않습니다.";
        errorBox.style.display = "block";
        return;
      }

      // 로그인 성공 → localStorage 저장
      localStorage.setItem("belong_user", json.data.username);

      // 메인 페이지로 이동
      window.location.href = "/";
    } catch (err) {
      console.error(err);
      errorBox.innerText = "서버와 연결할 수 없습니다.";
      errorBox.style.display = "block";
    }
  });
});
