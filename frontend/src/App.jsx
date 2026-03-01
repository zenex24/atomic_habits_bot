import { useEffect, useMemo, useState } from "react";
import TabBar from "./components/TabBar";
import HomeTab from "./tabs/HomeTab";
import ChatTab from "./tabs/ChatTab";
import PlanTab from "./tabs/PlanTab";
import ChallengesTab from "./tabs/ChallengesTab";
import ProfileTab from "./tabs/ProfileTab";
import { apiRequest, authTelegram } from "./lib/api";

const goodHabits = ["Начать читать", "Правильно питаться", "Заниматься спортом", "Бегать по утрам"];
const badHabits = ["Курение", "Алкоголь", "Дрочка", "Дешевый дофамин"];

const defaultProfile = {
  name: "",
  timezone: "Europe/Moscow",
  mentor_mode: "neutral",
  daily_reminder_time: "09:00",
};

export default function App() {
  const [activeTab, setActiveTab] = useState("home");
  const [authed, setAuthed] = useState(false);
  const [profile, setProfile] = useState(defaultProfile);
  const [stats, setStats] = useState(null);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [onboardingError, setOnboardingError] = useState("");
  const [onboardingSubmitting, setOnboardingSubmitting] = useState(false);
  const [onboarding, setOnboarding] = useState({
    name: "",
    good: [],
    bad: [],
    other: "",
    details: "",
    mentor_mode: "neutral",
  });

  const isOnboardingValid = useMemo(() => {
    const anyHabitSelected = onboarding.good.length > 0 || onboarding.bad.length > 0 || onboarding.other.trim();
    return onboarding.name.trim().length > 1 && anyHabitSelected;
  }, [onboarding]);

  useEffect(() => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  useEffect(() => {
    async function bootstrap() {
      const auth = await authTelegram();
      localStorage.setItem("ah_token", auth.access_token);
      setProfile(auth.profile);
      setAuthed(true);
      if (!auth.profile.onboarding_done) {
        setOnboardingOpen(true);
      } else {
        const metrics = await apiRequest("/api/v1/profile/stats");
        setStats(metrics);
      }
    }

    bootstrap().catch((e) => {
      console.error(e);
    });
  }, []);

  function toggleHabit(type, title) {
    setOnboarding((prev) => {
      const list = prev[type];
      return {
        ...prev,
        [type]: list.includes(title) ? list.filter((x) => x !== title) : [...list, title],
      };
    });
  }

  async function submitOnboarding() {
    if (!isOnboardingValid) {
      setOnboardingError("Заполни имя и выбери хотя бы одну привычку.");
      return;
    }
    setOnboardingSubmitting(true);
    setOnboardingError("");
    try {
      await apiRequest("/api/v1/onboarding", "POST", {
        name: onboarding.name,
        good_habits: onboarding.good,
        bad_habits: onboarding.bad,
        other_habit: onboarding.other.trim(),
        details: onboarding.details.trim(),
        mentor_mode: onboarding.mentor_mode,
      });
      setOnboardingOpen(false);
      const profileData = await apiRequest("/api/v1/profile");
      const statsData = await apiRequest("/api/v1/profile/stats");
      setProfile(profileData.profile);
      setStats(statsData);
    } catch (e) {
      setOnboardingError(e.message);
    } finally {
      setOnboardingSubmitting(false);
    }
  }

  if (!authed) {
    return (
      <main className="app-shell">
        <p className="loading">Загрузка Mini App...</p>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <div className="background-pattern" />
      <section className="app-frame">
        {activeTab === "home" && <HomeTab profile={profile} stats={stats} />}
        {activeTab === "chat" && <ChatTab mentorMode={profile.mentor_mode} />}
        {activeTab === "plan" && <PlanTab />}
        {activeTab === "challenges" && <ChallengesTab />}
        {activeTab === "profile" && <ProfileTab profile={profile} setProfile={setProfile} stats={stats} />}
      </section>
      <TabBar activeTab={activeTab} setActiveTab={setActiveTab} />

      {onboardingOpen ? (
        <div className="onboarding-overlay">
          <section className="onboarding-modal">
            <h2>Добро пожаловать</h2>
            <p>Настроим привычки и создадим персональный план.</p>

            <label>
              Как тебя зовут?
              <input
                value={onboarding.name}
                onChange={(e) => setOnboarding((prev) => ({ ...prev, name: e.target.value }))}
                maxLength={60}
              />
            </label>

            <div className="habit-block">
              <h3>Хочу привить хорошие привычки</h3>
              <div className="chip-row">
                {goodHabits.map((habit) => (
                  <button
                    type="button"
                    key={habit}
                    className={`chip ${onboarding.good.includes(habit) ? "selected" : ""}`}
                    onClick={() => toggleHabit("good", habit)}
                  >
                    {habit}
                  </button>
                ))}
              </div>
            </div>

            <div className="habit-block">
              <h3>Хочу убрать плохие привычки</h3>
              <div className="chip-row">
                {badHabits.map((habit) => (
                  <button
                    type="button"
                    key={habit}
                    className={`chip ${onboarding.bad.includes(habit) ? "selected" : ""}`}
                    onClick={() => toggleHabit("bad", habit)}
                  >
                    {habit}
                  </button>
                ))}
              </div>
            </div>

            <label>
              Другое (до 300 символов)
              <textarea
                value={onboarding.other}
                onChange={(e) => setOnboarding((prev) => ({ ...prev, other: e.target.value.slice(0, 300) }))}
                maxLength={300}
              />
            </label>

            <label>
              Подробнее о привычке
              <textarea
                value={onboarding.details}
                onChange={(e) => setOnboarding((prev) => ({ ...prev, details: e.target.value.slice(0, 500) }))}
                maxLength={500}
              />
            </label>

            <label>
              Тон наставника
              <select
                value={onboarding.mentor_mode}
                onChange={(e) => setOnboarding((prev) => ({ ...prev, mentor_mode: e.target.value }))}
              >
                <option value="soft">Мягкий</option>
                <option value="neutral">Нейтральный</option>
                <option value="strict">Строгий</option>
              </select>
            </label>

            {onboardingError ? <p className="error-text">{onboardingError}</p> : null}

            <button className="primary-btn" onClick={submitOnboarding} disabled={onboardingSubmitting}>
              {onboardingSubmitting ? "Сохраняю..." : "Начать"}
            </button>
          </section>
        </div>
      ) : null}
    </main>
  );
}
