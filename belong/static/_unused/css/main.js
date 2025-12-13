const USE_MOCK = true;
const API_BASE = USE_MOCK ? "/mock" : "/api";

async function loadDashboard() {
  const tableContainer = document.getElementById("dashboard-table");
  if (!tableContainer) return; // 다른 페이지에서는 안 돌게

  try {
    const res = await fetch(`${API_BASE}/population.json`);
    const json = await res.json();

    if (json.status !== "success") {
      tableContainer.innerText = "데이터 로드 실패";
      return;
    }

    const data = json.data;
    const rows = data.map(item => {
      return `
        <tr>
          <td>${item.region}</td>
          <td>${item.latest_value.toLocaleString()}</td>
          <td>${(item.growth_rate * 100).toFixed(1)}%</td>
        </tr>
      `;
    }).join("");

    tableContainer.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>구</th>
            <th>최신 독거노인 인구</th>
            <th>증가율</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  } catch (e) {
    console.error(e);
    tableContainer.innerText = "에러 발생";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();

  // 스토리 패널 페이드 인
  const panels = document.querySelectorAll(".story-panel");
  if (panels.length > 0 && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.35 }
    );
    panels.forEach((panel) => observer.observe(panel));
  }
});
let next = document.querySelector(".next");
let prev = document.querySelector(".prev");

next.addEventListener("click", function () {
  let items = document.querySelectorAll(".item");
  document.querySelector(".slide").appendChild(items[0]);
});

prev.addEventListener("click", function () {
  let items = document.querySelectorAll(".item");
  document.querySelector(".slide").prepend(items[items.length - 1]);
});
