import { useEffect, useState } from "react";
import { apiRequest } from "../lib/api";

function PlanList({ title, items }) {
  return (
    <article className="card">
      <h3>{title}</h3>
      {items.length ? (
        <ul className="simple-list">
          {items.map((item) => (
            <li key={item.id || item.title}>{item.title}</li>
          ))}
        </ul>
      ) : (
        <p>Пока пусто</p>
      )}
    </article>
  );
}

export default function PlanTab() {
  const [daily, setDaily] = useState([]);
  const [weekly, setWeekly] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadPlans() {
    try {
      const [dailyData, weeklyData] = await Promise.all([
        apiRequest("/api/v1/plan/daily"),
        apiRequest("/api/v1/plan/weekly"),
      ]);
      setDaily(dailyData.items);
      setWeekly(weeklyData.items);
    } catch (e) {
      setError(e.message);
    }
  }

  async function generatePlan() {
    setLoading(true);
    setError("");
    try {
      await apiRequest("/api/v1/plan/generate", "POST", {});
      await loadPlans();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPlans();
  }, []);

  return (
    <section className="tab-content">
      <button className="primary-btn" onClick={generatePlan} disabled={loading}>
        {loading ? "Генерирую..." : "Сгенерировать AI-план"}
      </button>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="card-grid">
        <PlanList title="Ежедневный план" items={daily} />
        <PlanList title="Недельный план" items={weekly} />
      </div>
    </section>
  );
}
