const API_BASE = new URLSearchParams(location.search).get("api_base") || window.APP_CONFIG?.API_BASE || "";
const token = new URLSearchParams(location.search).get("token");

function el(id) {
  return document.getElementById(id);
}

async function loadMetrics() {
  const res = await fetch(`${API_BASE}/api/admin/metrics?token=${encodeURIComponent(token || "")}`);
  if (!res.ok) throw new Error("Не удалось загрузить метрики");
  return res.json();
}

async function loadUsers() {
  const res = await fetch(`${API_BASE}/api/admin/users?token=${encodeURIComponent(token || "")}`);
  if (!res.ok) throw new Error("Не удалось загрузить пользователей");
  return res.json();
}

function renderMetrics(data) {
  const metricsBox = el("metricsBox");
  metricsBox.innerHTML = "";

  const items = [
    ["Всего пользователей", data.total_users],
    ["С онбордингом", data.onboarding_completed_users],
    ["DAU", data.dau],
    ["Средний стрик", data.avg_streak],
    ["Completion rate 7d", `${data.completion_rate_7d}%`],
    ["Retention D1", `${data.retention_d1}%`],
    ["Retention D7", `${data.retention_d7}%`]
  ];

  items.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "item";
    row.innerHTML = `<strong>${label}:</strong> ${value}`;
    metricsBox.appendChild(row);
  });
}

function renderUsers(users) {
  const usersBox = el("usersBox");
  usersBox.innerHTML = "";

  if (!users.length) {
    usersBox.innerHTML = '<div class="item">Нет данных</div>';
    return;
  }

  users.forEach((u) => {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <strong>${u.display_name || "Без имени"}</strong>
      <p class="muted">ID: ${u.telegram_id}</p>
      <p class="muted">Цель: ${u.goal_type || "-"}; Привычка: ${u.habit_name || "-"}</p>
      <p class="muted">Серия: ${u.streak_days}; Онбординг: ${u.onboarding_completed ? "да" : "нет"}</p>
      <p class="muted">Последняя активность: ${u.last_active_at}</p>
    `;
    usersBox.appendChild(div);
  });
}

async function init() {
  el("backBtn").onclick = () => {
    location.href = "./index.html";
  };

  if (!token) {
    alert("Нужен token в query параметре");
    return;
  }

  try {
    const [metrics, users] = await Promise.all([loadMetrics(), loadUsers()]);
    renderMetrics(metrics);
    renderUsers(users);
  } catch (err) {
    alert(err.message);
  }
}

init();
