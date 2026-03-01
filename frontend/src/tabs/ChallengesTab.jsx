import { useEffect, useState } from "react";
import { apiRequest } from "../lib/api";

const challengeTypes = [
  { kind: "seven", title: "7 дней подряд" },
  { kind: "fourteen", title: "14 дней фокуса" },
  { kind: "thirty", title: "30 дней трансформации" },
  { kind: "no_skip", title: "Без пропусков" },
];

export default function ChallengesTab() {
  const [active, setActive] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const data = await apiRequest("/api/v1/challenges");
      setActive(data.items);
    } catch (e) {
      setError(e.message);
    }
  }

  async function join(kind) {
    try {
      await apiRequest("/api/v1/challenges/join", "POST", { kind });
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <section className="tab-content">
      <div className="card-grid">
        {challengeTypes.map((challenge) => (
          <article className="card" key={challenge.kind}>
            <h3>{challenge.title}</h3>
            <button className="secondary-btn" onClick={() => join(challenge.kind)}>
              Присоединиться
            </button>
          </article>
        ))}
      </div>
      <article className="card">
        <h3>Активные челленджи</h3>
        {active.length ? (
          <ul className="simple-list">
            {active.map((item) => (
              <li key={item.id}>
                {item.title}: день {item.current_day}/{item.days_total}
              </li>
            ))}
          </ul>
        ) : (
          <p>Нет активных челленджей.</p>
        )}
      </article>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
