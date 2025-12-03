// static/js/signup.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signup-form");
  const errorBox = document.getElementById("signup-error");
  const pwMsg = document.getElementById("pw-match-msg");
  const pw1Input = document.getElementById("password1");
  const pw2Input = document.getElementById("password2");

  if (!form) return;

  function checkPasswordMatch() {
    const pw1 = pw1Input.value;
    const pw2 = pw2Input.value;

    if (!pw2) {
      pwMsg.style.display = "none";
      return;
    }

    pwMsg.style.display = "inline";

    if (pw1 === pw2) {
      pwMsg.classList.remove("text-danger");
      pwMsg.classList.add("text-success");
      pwMsg.innerText = "비밀번호가 일치합니다.";
    } else {
      pwMsg.classList.remove("text-success");
      pwMsg.classList.add("text-danger");
      pwMsg.innerText = "비밀번호가 일치하지 않습니다.";
    }
  }

  pw1Input.addEventListener("input", checkPasswordMatch);
  pw2Input.addEventListener("input", checkPasswordMatch);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password1 = pw1Input.value.trim();
    const password2 = pw2Input.value.trim();

    errorBox.style.display = "none";

    if (!password1 || !password2) {
      errorBox.innerText = "비밀번호를 모두 입력해주세요.";
      errorBox.style.display = "block";
      return;
    }

    if (password1 !== password2) {
      errorBox.innerText = "비밀번호가 서로 일치하지 않습니다.";
      errorBox.style.display = "block";
      checkPasswordMatch();
      return;
    }

    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          password: password1,
        }),
      });

      const json = await res.json();

      if (!res.ok || json.status !== "success") {
        errorBox.innerText = json.message || "이미 가입된 회원입니다.";
        errorBox.style.display = "block";
        return;
      }

      // 회원가입 성공 → 메인 페이지로 이동
      window.location.href = "/";
    } catch (err) {
       console.error("fetch 또는 JSON 파싱 에러:", err);
       alert("클라이언트 에러: " + err);  // 임시
       errorBox.innerText = "서버와의 통신 중 오류가 발생했습니다.";
       errorBox.style.display = "block";
    }
  });
});
