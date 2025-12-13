// static/js/navbar.js
document.addEventListener("DOMContentLoaded", () => {
  const navLogin = document.getElementById("nav-login");
  const navSignup = document.getElementById("nav-signup");
  const navUser = document.getElementById("nav-user");
  const navUsername = document.getElementById("nav-username");
  const logoutBtn = document.getElementById("logout-btn");

  let user = null;
  try {
    user = JSON.parse(localStorage.getItem("belong_user") || "null");
  } catch (e) {
    user = null;
  }

  if (user && user.username) {
    navLogin?.classList.add("d-none");
    navSignup?.classList.add("d-none");
    navUser?.classList.remove("d-none");
    if (navUsername) navUsername.textContent = user.username;

    logoutBtn?.addEventListener("click", () => {
      localStorage.removeItem("belong_user");
    });
  } else {
    navLogin?.classList.remove("d-none");
    navSignup?.classList.remove("d-none");
    navUser?.classList.add("d-none");
  }
});
