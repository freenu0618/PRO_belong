// static/js/login.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");
  const errorBox = document.getElementById("login-error");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username")?.value?.trim() || "";
    const password = document.getElementById("password")?.value?.trim() || "";

    if (errorBox) {
      errorBox.style.display = "none";
      errorBox.innerText = "";
    }

    if (!username || !password) {
      if (errorBox) {
        errorBox.innerText = "아이디와 비밀번호를 입력해주세요.";
        errorBox.style.display = "block";
      }
      return;
    }

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const json = await res.json().catch(() => null);

      // ✅ 새 API 응답 형식: {ok: true, data: {...}}
      if (!res.ok || !json || json.ok !== true) {
        const msg = json?.error?.message || json?.message || "아이디 또는 비밀번호가 올바르지 않습니다.";
        if (errorBox) {
          errorBox.innerText = msg;
          errorBox.style.display = "block";
        }
        return;
      }

      const token = json?.data?.access_token;
      const user = json?.data?.user;

      // ✅ 핵심: access_token 저장 (auth_ui.js가 이 키를 봄)
      if (!token) {
        if (errorBox) {
          errorBox.innerText = "로그인 응답에 access_token이 없습니다. (서버 응답 확인 필요)";
          errorBox.style.display = "block";
        }
        return;
      }

      localStorage.setItem("access_token", token);

      // (선택) 사용자 정보도 저장해두면 UI에서 바로 활용 가능
      if (user) {
        localStorage.setItem("belong_user", JSON.stringify(user));
      } else {
        localStorage.removeItem("belong_user");
      }

      // 메인 페이지로 이동
      window.location.href = "/";
    } catch (err) {
      console.error(err);
      if (errorBox) {
        errorBox.innerText = "서버와 연결할 수 없습니다.";
        errorBox.style.display = "block";
      }
    }
  });
});
