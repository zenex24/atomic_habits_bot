import { useEffect, useState } from 'react'

import { request } from '../api'

export function ProfilePage({ profile, onProfile }) {
  const [tone, setTone] = useState(profile?.mentor_tone || 'friendly')
  const [reminder, setReminder] = useState({ daily_time: '09:00', text: 'Time to work on your habit plan.', enabled: true })
  const [error, setError] = useState('')

  useEffect(() => {
    if (profile?.mentor_tone) {
      setTone(profile.mentor_tone)
    }
  }, [profile?.mentor_tone])

  const saveTone = async () => {
    try {
      setError('')
      await request('/profile/mentor-tone', {
        method: 'POST',
        body: JSON.stringify({ tone }),
      })
      onProfile((prev) => ({ ...prev, mentor_tone: tone }))
    } catch (err) {
      setError(err.message)
    }
  }

  const loadReminder = async () => {
    try {
      const data = await request('/profile/reminder')
      if (data) setReminder(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const saveReminder = async () => {
    try {
      setError('')
      const data = await request('/profile/reminder', {
        method: 'POST',
        body: JSON.stringify(reminder),
      })
      setReminder(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const activateDev = async () => {
    try {
      await request('/billing/dev-activate', { method: 'POST' })
      const data = await request('/profile/me')
      onProfile(data)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    loadReminder()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <section className="page">
      <h1>Profile</h1>
      <p>Name: {profile?.full_name || 'Not set'}</p>
      <p>Subscription: {profile?.is_paid ? 'Active' : 'Inactive'}</p>

      <article className="card">
        <h3>Mentor tone</h3>
        <select value={tone} onChange={(e) => setTone(e.target.value)}>
          <option value="friendly">Friendly</option>
          <option value="strict">Strict</option>
          <option value="balanced">Balanced</option>
        </select>
        <button onClick={saveTone}>Save tone</button>
      </article>

      <article className="card">
        <h3>Reminder</h3>
        <label>
          Daily time
          <input
            type="time"
            value={reminder.daily_time}
            onChange={(e) => setReminder((prev) => ({ ...prev, daily_time: e.target.value }))}
          />
        </label>
        <label>
          Text
          <input
            value={reminder.text}
            onChange={(e) => setReminder((prev) => ({ ...prev, text: e.target.value }))}
          />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={reminder.enabled}
            onChange={(e) => setReminder((prev) => ({ ...prev, enabled: e.target.checked }))}
          />
          Enabled
        </label>
        <button onClick={saveReminder}>Save reminder</button>
      </article>

      {!profile?.is_paid && <button onClick={activateDev}>Activate local subscription</button>}

      {error && <div className="error">{error}</div>}
    </section>
  )
}
