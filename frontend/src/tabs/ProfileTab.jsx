import { useState } from "react";
import { apiRequest } from "../lib/api";

export default function ProfileTab({ profile, setProfile, stats }) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function saveProfile() {
    setSaving(true);
    setError("");
    try {
      const data = await apiRequest("/api/v1/profile", "PATCH", {
        daily_reminder_time: profile.daily_reminder_time,
        timezone: profile.timezone,
        mentor_mode: profile.mentor_mode,
      });
      setProfile((prev) => ({ ...prev, ...data.profile }));
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="tab-content">
      <article className="card">
        <h3>Параметры</h3>
        <label>
          Время напоминания
          <input
            type="time"
            value={profile.daily_reminder_time || "09:00"}
            onChange={(e) => setProfile((prev) => ({ ...prev, daily_reminder_time: e.target.value }))}
          />
        </label>
        <label>
          Часовой пояс
          <input
            type="text"
            value={profile.timezone || "Europe/Moscow"}
            onChange={(e) => setProfile((prev) => ({ ...prev, timezone: e.target.value }))}
          />
        </label>
        <label>
          Режим наставника
          <select
            value={profile.mentor_mode || "neutral"}
            onChange={(e) => setProfile((prev) => ({ ...prev, mentor_mode: e.target.value }))}
          >
            <option value="soft">Мягкий</option>
            <option value="neutral">Нейтральный</option>
            <option value="strict">Строгий</option>
          </select>
        </label>
        <button className="primary-btn" onClick={saveProfile} disabled={saving}>
          {saving ? "Сохраняю..." : "Сохранить"}
        </button>
        {error ? <p className="error-text">{error}</p> : null}
      </article>
      <article className="card">
        <h3>Статистика</h3>
        <p>Стрик: {stats?.streak_days ?? 0} дней</p>
        <p>Выполнение за 7 дней: {stats?.completion_rate_7d ?? 0}%</p>
        <p>Завершенные челленджи: {stats?.completed_challenges ?? 0}</p>
        <p>Уровень: {stats?.level ?? 1}</p>
      </article>
    </section>
  );
}
