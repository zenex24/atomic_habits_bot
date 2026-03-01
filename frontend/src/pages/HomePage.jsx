const DAILY_TIPS = [
  'Make it obvious: set a clear cue for today\'s habit.',
  'Make it easy: reduce friction for the first 2-minute action.',
  'Never miss twice: if you skipped yesterday, do a tiny version today.',
  'Stack habits: attach one small action to your current routine.',
]

export function HomePage({ profile, plan }) {
  const todayTip = DAILY_TIPS[new Date().getDate() % DAILY_TIPS.length]
  const nextTask = plan?.tasks?.find((task) => task.status === 'not_started')

  return (
    <section className="page">
      <h1>Main</h1>
      <div className="card-grid">
        <article className="card">
          <h3>Progress</h3>
          <p>Streak: {profile?.stats?.streak_days || 0} days</p>
          <p>Completed tasks: {profile?.stats?.completed_tasks || 0}</p>
          <p>Total points: {profile?.stats?.total_points || 0}</p>
        </article>

        <article className="card">
          <h3>Next step</h3>
          {nextTask ? (
            <>
              <p>{nextTask.title}</p>
              <small>Due: {nextTask.due_date}</small>
            </>
          ) : (
            <p>Generate your plan in Plan tab.</p>
          )}
        </article>

        <article className="card card-wide">
          <h3>Atomic Habits tip</h3>
          <p>{todayTip}</p>
        </article>
      </div>
    </section>
  )
}
