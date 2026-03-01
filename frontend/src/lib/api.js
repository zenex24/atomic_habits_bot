const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const DEV_TELEGRAM_ID = import.meta.env.VITE_DEV_TELEGRAM_ID || "999001";
const DEV_NAME = import.meta.env.VITE_DEV_NAME || "Тестовый пользователь";

function getTelegramInitData() {
  if (window.Telegram?.WebApp?.initData) {
    return window.Telegram.WebApp.initData;
  }
  return "";
}

export async function authTelegram() {
  const initData = getTelegramInitData();
  const payload = initData
    ? { init_data: initData }
    : { init_data: "", dev_telegram_id: Number(DEV_TELEGRAM_ID), dev_name: DEV_NAME };
  const response = await fetch(`${API_URL}/api/v1/auth/telegram-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Не удалось авторизоваться");
  }
  return response.json();
}

export async function apiRequest(path, method = "GET", body = null) {
  const token = localStorage.getItem("ah_token");
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
    },
    body: body ? JSON.stringify(body) : null,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Ошибка запроса");
  }
  return data;
}
