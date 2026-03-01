export default function HomeTab({ profile, stats }) {
  return (
    <section className="tab-content">
      <div className="hero">
        <p className="hero-kicker">Atomic Habits Coach</p>
        <h1>{profile?.name ? `${profile.name}, двигаемся маленькими шагами` : "Начни сегодня"}</h1>
        <p>1% улучшения каждый день превращается в большой результат.</p>
      </div>

      <div className="card-grid">
        <article className="card">
          <h3>Текущий стрик</h3>
          <p className="metric">{stats?.streak_days ?? 0} дней</p>
        </article>
        <article className="card">
          <h3>Выполнение 7 дней</h3>
          <p className="metric">{stats?.completion_rate_7d ?? 0}%</p>
        </article>
        <article className="card">
          <h3>Завершено челленджей</h3>
          <p className="metric">{stats?.completed_challenges ?? 0}</p>
        </article>
      </div>
    </section>
  );
}
