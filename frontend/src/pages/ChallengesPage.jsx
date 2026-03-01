import { useState } from 'react'

import { request } from '../api'

export function ChallengesPage({ challenges, onChallenges }) {
  const [title, setTitle] = useState('')
  const [duration, setDuration] = useState(21)
  const [error, setError] = useState('')

  const create = async (event) => {
    event.preventDefault()
    try {
      const created = await request('/challenges', {
        method: 'POST',
        body: JSON.stringify({ title, duration_days: Number(duration) }),
      })
      onChallenges((prev) => [created, ...prev])
      setTitle('')
    } catch (err) {
      setError(err.message)
    }
  }

  const checkin = async (challengeId, status) => {
    try {
      const updated = await request(`/challenges/${challengeId}/checkin`, {
        method: 'POST',
        body: JSON.stringify({ status }),
      })
      onChallenges((prev) => prev.map((item) => (item.id === challengeId ? updated : item)))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="page">
      <h1>Challenges</h1>

      <form className="inline-form" onSubmit={create}>
        <input
          placeholder="Challenge title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          minLength={3}
          maxLength={180}
        />
        <input
          type="number"
          min={3}
          max={120}
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
        />
        <button type="submit">Create</button>
      </form>

      {error && <div className="error">{error}</div>}

      <div className="plan-list">
        {challenges.map((challenge) => (
          <article className="card" key={challenge.id}>
            <h3>{challenge.title}</h3>
            <p>
              {challenge.start_date} - {challenge.end_date}
            </p>
            <p>Points: {challenge.reward_points}</p>
            <div className="inline-actions">
              <button onClick={() => checkin(challenge.id, 'completed')}>Complete today</button>
              <button onClick={() => checkin(challenge.id, 'missed')}>Missed</button>
              <button onClick={() => checkin(challenge.id, 'save')}>Use monthly save</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
