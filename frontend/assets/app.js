function getTelegramWebApp() {
  return window.Telegram?.WebApp;
}

const tg = getTelegramWebApp();
if (tg) {
  tg.ready();
  tg.expand();
}

const state = {
  bootstrap: null,
  plan: [],
  challenges: [],
  profile: null,
  chat: []
};
const onboardingState = {
  initialized: false,
  steps: [],
  current: 0,
  mode: "initial"
};
let eventsBound = false;

const API_BASE = new URLSearchParams(location.search).get("api_base") || window.APP_CONFIG?.API_BASE || "";
const WEBAPP_AUTH_TOKEN = new URLSearchParams(location.search).get("auth_token") || "";
const TEST_USER_ID = new URLSearchParams(location.search).get("test_user_id");

function el(id) {
  return document.getElementById(id);
}

async function waitForInitData(timeoutMs = 350, intervalMs = 50) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const value = getTelegramWebApp()?.initData || "";
    if (value) {
      return value;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  return getTelegramWebApp()?.initData || "";
}

async function api(path, options = {}) {
  const headers = {
    ...(options.headers || {})
  };

  const initData = getTelegramWebApp()?.initData || "";
  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  }
  if (WEBAPP_AUTH_TOKEN) {
    headers["X-WebApp-Auth-Token"] = WEBAPP_AUTH_TOKEN;
  }
  if (TEST_USER_ID) {
    headers["X-Test-User-Id"] = TEST_USER_ID;
  }
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}

function showTab(tabName) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.id === `tab-${tabName}`);
  });
  document.querySelectorAll(".bottom-nav button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });
}

function renderHome() {
  const home = state.bootstrap?.home;
  if (!home) return;

  el("habitTitle").textContent = home.habit_name || "Привычка пока не выбрана";
  el("goalTypeText").textContent = home.goal_type === "build"
    ? "Цель: привить хорошую привычку"
    : home.goal_type === "break"
      ? "Цель: убрать плохую привычку"
      : "Настройте цель в профиле";
  el("streakDays").textContent = String(home.streak_days || 0);
  el("bestStreak").textContent = String(home.best_streak || 0);
  const progress = home.plan_progress || { done: 0, total: 0 };
  el("planProgress").textContent = `${progress.done}/${progress.total}`;

  const welcomeName = state.bootstrap?.user?.display_name || "друг";
  el("welcomeTitle").textContent = `Здравствуйте, ${welcomeName}`;
}

function renderPlan() {
  const container = el("planList");
  container.innerHTML = "";

  if (!state.plan.length) {
    container.innerHTML = '<div class="item"><p class="muted">Пока нет пунктов плана.</p></div>';
    return;
  }

  state.plan.forEach((item) => {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <h4>${escapeHtml(item.title)}</h4>
      <p class="muted">${escapeHtml(item.description || "Без описания")}</p>
      <div class="item-actions">
        <button class="primary">${item.is_done ? "Отменить выполнение" : "Отметить выполненным"}</button>
        <button class="danger">Удалить</button>
      </div>
    `;

    const [toggleBtn, deleteBtn] = div.querySelectorAll("button");
    toggleBtn.onclick = async () => {
      try {
        await api(`/api/plan/items/${item.id}`, {
          method: "PATCH",
          body: JSON.stringify({ is_done: !item.is_done })
        });
        await loadPlan();
        await loadBootstrap();
      } catch (e) {
        alert(e.message);
      }
    };

    deleteBtn.onclick = async () => {
      try {
        await api(`/api/plan/items/${item.id}`, { method: "DELETE" });
        await loadPlan();
        await loadBootstrap();
      } catch (e) {
        alert(e.message);
      }
    };

    container.appendChild(div);
  });
}

function renderChallenges() {
  const container = el("challengeList");
  container.innerHTML = "";

  if (!state.challenges.length) {
    container.innerHTML = '<div class="item"><p class="muted">Челленджей пока нет.</p></div>';
    return;
  }

  state.challenges.forEach((item) => {
    const div = document.createElement("div");
    div.className = "item";
    const status = item.is_completed
      ? "Завершен"
      : item.joined
        ? `В процессе: ${item.progress_days}/${item.duration_days}`
        : "Не начат";

    div.innerHTML = `
      <h4>${escapeHtml(item.title)}</h4>
      <p>${escapeHtml(item.description)}</p>
      <p class="muted">${status} · ${item.points} очков</p>
      <div class="item-actions"></div>
    `;

    const actions = div.querySelector(".item-actions");
    if (!item.joined) {
      const btn = document.createElement("button");
      btn.className = "primary";
      btn.textContent = "Вступить";
      btn.onclick = async () => {
        try {
          await api(`/api/challenges/${item.id}/join`, { method: "POST" });
          await loadChallenges();
          await loadBootstrap();
        } catch (e) {
          alert(e.message);
        }
      };
      actions.appendChild(btn);
    } else if (!item.is_completed) {
      const btn = document.createElement("button");
      btn.className = "primary";
      btn.textContent = "Отметить день";
      btn.onclick = async () => {
        try {
          await api(`/api/challenges/${item.id}/progress`, { method: "POST" });
          await loadChallenges();
          await loadBootstrap();
        } catch (e) {
          alert(e.message);
        }
      };
      actions.appendChild(btn);
    }

    container.appendChild(div);
  });
}

function renderProfile() {
  const p = state.profile;
  if (!p) return;

  const goalText = p.goal_type === "build"
    ? "Привить привычку"
    : p.goal_type === "break"
      ? "Убрать привычку"
      : "Не выбрана";

  el("profileSummaryName").textContent = p.display_name || "Не указано";
  el("profileSummaryGoal").textContent = goalText;
  el("profileSummaryHabit").textContent = p.habit_name || "Не указана";

  el("profileName").value = p.display_name || "";
  el("profileTone").value = p.mentor_tone || "neutral";
  el("profileReminder").value = p.reminder_time || "09:00";
  el("profileTimezone").value = p.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  el("profileDetails").value = p.habit_details || "";

  el("profileStats").textContent = `Текущая серия: ${p.streak_days || 0} · Лучший стрик: ${p.best_streak || 0}`;
}

function addChatMessage(role, text) {
  const box = el("chatBox");
  const div = document.createElement("div");
  div.className = `chat-msg ${role}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function renderChat() {
  const box = el("chatBox");
  box.innerHTML = "";
  if (!state.chat.length) {
    addChatMessage("assistant", "Здравствуйте. Я ваш наставник по привычкам. Сформулируйте задачу на сегодня.");
    return;
  }

  state.chat.forEach((msg) => addChatMessage(msg.role, msg.text));
}

async function loadBootstrap() {
  state.bootstrap = await api("/api/bootstrap");
  renderHome();

  if (!state.bootstrap.onboarding_completed) {
    setOnboardingMode("initial");
    el("onboardingOverlay").classList.remove("hidden");
    resetOnboardingStepper();
  } else {
    el("onboardingOverlay").classList.add("hidden");
  }
}

async function loadPlan() {
  state.plan = await api("/api/plan");
  renderPlan();
}

async function loadChallenges() {
  state.challenges = await api("/api/challenges");
  renderChallenges();
}

async function loadProfile() {
  state.profile = await api("/api/profile");
  renderProfile();
}

function updateGoalDependentTexts() {
  const isBuild = el("obGoal").value === "build";

  el("obHabitNameLabel").textContent = isBuild
    ? "Какую привычку хотите привить?"
    : "Какую привычку хотите убрать?";
  el("obHabitName").placeholder = isBuild
    ? "Например: читать 10 минут перед сном"
    : "Например: курение";

  el("obHabitDetailsLabel").textContent = isBuild
    ? "Подробнее опишите привычку"
    : "Подробнее опишите, как проявляется эта привычка";
  el("obHabitDetails").placeholder = isBuild
    ? "Что именно хотите добавить в жизнь"
    : "В каких ситуациях это чаще происходит";

  el("obBaselineLabel").textContent = isBuild
    ? "Как часто хотите делать эту привычку?"
    : "Как часто происходит эта привычка?";
  el("obBaseline").placeholder = isBuild
    ? "Например: каждый день"
    : "Например: 3 раза в день";

  el("obMotivationLabel").textContent = isBuild
    ? "Почему это важно для вас?"
    : "Почему важно убрать эту привычку?";
  el("obMotivation").placeholder = isBuild
    ? "Что это даст в вашей жизни"
    : "Что улучшится, когда вы избавитесь от этой привычки";
}

function setOnboardingMode(mode) {
  onboardingState.mode = mode === "reconfigure" ? "reconfigure" : "initial";

  const titleEl = el("onboardingTitle");
  const subtitleEl = el("onboardingSubtitle");
  const submitBtn = el("obSubmitBtn");
  if (!titleEl || !subtitleEl || !submitBtn) return;

  if (onboardingState.mode === "reconfigure") {
    titleEl.textContent = "Изменение профиля";
    subtitleEl.textContent = "Измените ответы. После подтверждения прогресс, план, чат и челленджи будут сброшены.";
    submitBtn.textContent = "Подтвердить изменения";
    return;
  }

  titleEl.textContent = "Первый запуск";
  subtitleEl.textContent = "Ответьте на вопросы, чтобы настроить персональный трек привычки.";
  submitBtn.textContent = "Завершить настройку";
}

function fillOnboardingFromProfile(profile) {
  if (!profile) return;

  el("obName").value = profile.display_name || state.bootstrap?.user?.display_name || "";
  el("obGoal").value = profile.goal_type || "build";
  updateGoalDependentTexts();

  el("obHabitName").value = profile.habit_name || "";
  el("obHabitDetails").value = profile.habit_details || "";
  el("obMotivation").value = profile.motivation || "";
  el("obBaseline").value = profile.baseline_frequency || "";
  el("obTone").value = profile.mentor_tone || "neutral";
  el("obReminder").value = profile.reminder_time || "09:00";
  el("obTimezone").value = profile.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  el("obPrivacy").checked = true;
}

function showOnboardingStep(index) {
  const steps = onboardingState.steps;
  if (!steps.length) return;

  onboardingState.current = Math.max(0, Math.min(index, steps.length - 1));

  steps.forEach((step, i) => {
    step.classList.toggle("hidden", i !== onboardingState.current);
  });

  el("obProgress").textContent = `Вопрос ${onboardingState.current + 1} из ${steps.length}`;
  el("obPrevBtn").classList.toggle("hidden", onboardingState.current === 0);
  el("obNextBtn").classList.toggle("hidden", onboardingState.current === steps.length - 1);
  el("obSubmitBtn").classList.toggle("hidden", onboardingState.current !== steps.length - 1);
}

function validateOnboardingStep(index) {
  const step = onboardingState.steps[index];
  if (!step) return true;

  const fields = step.querySelectorAll("input, textarea, select");
  for (const field of fields) {
    if (!field.checkValidity()) {
      field.reportValidity();
      return false;
    }
  }

  return true;
}

function initOnboardingStepper() {
  if (onboardingState.initialized) return;

  onboardingState.steps = Array.from(document.querySelectorAll("#onboardingForm .ob-step"));
  onboardingState.initialized = true;

  el("obPrevBtn").onclick = () => showOnboardingStep(onboardingState.current - 1);
  el("obNextBtn").onclick = () => {
    if (!validateOnboardingStep(onboardingState.current)) return;
    showOnboardingStep(onboardingState.current + 1);
  };

  showOnboardingStep(0);
}

function resetOnboardingStepper() {
  if (!onboardingState.initialized) return;
  showOnboardingStep(0);
}

function openOnboardingForReconfigure() {
  if (!state.profile) {
    alert("Профиль еще не загружен. Попробуйте снова через пару секунд.");
    return;
  }

  setOnboardingMode("reconfigure");
  fillOnboardingFromProfile(state.profile);
  el("onboardingOverlay").classList.remove("hidden");
  resetOnboardingStepper();
}

function setupEvents() {
  if (eventsBound) return;
  eventsBound = true;

  el("obGoal").onchange = updateGoalDependentTexts;

  document.querySelectorAll(".bottom-nav button").forEach((btn) => {
    btn.onclick = () => showTab(btn.dataset.tab);
  });

  el("checkinDoneBtn").onclick = () => submitCheckin(true);
  el("checkinMissedBtn").onclick = () => submitCheckin(false);

  el("chatForm").onsubmit = async (e) => {
    e.preventDefault();
    const input = el("chatInput");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    state.chat.push({ role: "user", text: message });
    renderChat();

    try {
      const data = await api("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message })
      });
      state.chat.push({ role: "assistant", text: data.reply });
      renderChat();
      el("chatLimit").textContent = `Осталось сообщений сегодня: ${data.remaining_today}`;
    } catch (err) {
      alert(err.message);
    }
  };

  el("planForm").onsubmit = async (e) => {
    e.preventDefault();
    const title = el("planTitle").value.trim();
    const description = el("planDesc").value.trim();
    if (!title) return;

    try {
      await api("/api/plan/items", {
        method: "POST",
        body: JSON.stringify({ title, description })
      });
      el("planTitle").value = "";
      el("planDesc").value = "";
      await loadPlan();
      await loadBootstrap();
    } catch (err) {
      alert(err.message);
    }
  };

  el("profileForm").onsubmit = async (e) => {
    e.preventDefault();
    try {
      await api("/api/profile", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: el("profileName").value.trim(),
          mentor_tone: el("profileTone").value,
          reminder_time: el("profileReminder").value,
          timezone: el("profileTimezone").value.trim(),
          habit_details: el("profileDetails").value.trim()
        })
      });
      await loadProfile();
      await loadBootstrap();
      alert("Профиль обновлен");
    } catch (err) {
      alert(err.message);
    }
  };

  el("profileReconfigureBtn").onclick = openOnboardingForReconfigure;

  el("onboardingForm").onsubmit = async (e) => {
    e.preventDefault();

    const goalType = el("obGoal").value;
    const habitCategory = goalType === "build" ? "Полезная привычка" : "Вредная привычка";

    const isReconfigure = onboardingState.mode === "reconfigure";
    if (isReconfigure) {
      const confirmed = confirm(
        "Подтвердите изменения. Будут сброшены прогресс, текущий план, история чата и участие в челленджах."
      );
      if (!confirmed) return;
    }

    try {
      await api(isReconfigure ? "/api/profile/reconfigure" : "/api/onboarding", {
        method: "POST",
        body: JSON.stringify({
          display_name: el("obName").value.trim(),
          goal_type: goalType,
          habit_category: habitCategory,
          habit_name: el("obHabitName").value.trim(),
          habit_details: el("obHabitDetails").value.trim(),
          motivation: el("obMotivation").value.trim(),
          baseline_frequency: el("obBaseline").value.trim(),
          mentor_tone: el("obTone").value || "neutral",
          reminder_time: el("obReminder").value || "09:00",
          timezone: el("obTimezone").value.trim() || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
          privacy_accepted: el("obPrivacy").checked
        })
      });

      el("onboardingOverlay").classList.add("hidden");
      setOnboardingMode("initial");
      await Promise.all([loadBootstrap(), loadPlan(), loadChallenges(), loadProfile()]);
      if (isReconfigure) {
        alert("Профиль обновлен. Прогресс и связанные данные сброшены.");
      }
    } catch (err) {
      alert(err.message);
    }
  };

  el("openAdminBtn").onclick = () => {
    const token = prompt("Введите admin token");
    if (token) {
      location.href = `./admin.html?token=${encodeURIComponent(token)}`;
    }
  };
}

async function submitCheckin(completed) {
  try {
    await api("/api/plan/checkin", {
      method: "POST",
      body: JSON.stringify({ completed })
    });
    await loadBootstrap();
    await loadProfile();
    alert(completed ? "Отлично, отметка сохранена" : "Отметка сохранена. Вернитесь к минимальному шагу сегодня");
  } catch (err) {
    alert(err.message);
  }
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function initData() {
  const initData = WEBAPP_AUTH_TOKEN ? "" : await waitForInitData();
  if (!initData && !WEBAPP_AUTH_TOKEN && !TEST_USER_ID) {
    const platform = getTelegramWebApp()?.platform || "unknown";
    alert(
      `Telegram не передал initData (platform: ${platform}). ` +
      "Откройте mini app заново через /start. Нужна ссылка, где есть параметр auth_token=..."
    );
  }

  el("obTimezone").value = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  el("obReminder").value = "09:00";
  el("obTone").value = "neutral";

  updateGoalDependentTexts();
  setOnboardingMode("initial");
  initOnboardingStepper();
  setupEvents();

  // If backend is not configured yet, still show onboarding UI instead of empty main screen.
  if (!API_BASE) {
    el("onboardingOverlay").classList.remove("hidden");
  }

  try {
    await loadBootstrap();
    await Promise.all([loadPlan(), loadChallenges(), loadProfile()]);
    renderChat();
  } catch (err) {
    el("onboardingOverlay").classList.remove("hidden");
    const backendHint = !API_BASE
      ? "Не задан API_BASE в frontend/assets/config.js. Укажите публичный HTTPS URL backend."
      : "Проверьте доступность backend API и CORS.";
    alert(`Ошибка загрузки: ${err.message}. ${backendHint}`);
  }
}

initData();


