import { useMemo, useState } from 'react'

import { request } from '../api'

const CATEGORIES = [
  { value: 'sleep', label: 'Sleep' },
  { value: 'fitness', label: 'Fitness' },
  { value: 'nutrition', label: 'Nutrition' },
  { value: 'focus', label: 'Focus' },
  { value: 'digital_detox', label: 'Digital detox' },
  { value: 'mindfulness', label: 'Mindfulness' },
  { value: 'reading', label: 'Reading' },
  { value: 'finance', label: 'Finance' },
  { value: 'other', label: 'Other' },
]

export function OnboardingModal({ onDone }) {
  const [form, setForm] = useState({
    full_name: '',
    goal_type: 'build',
    habit_category: 'sleep',
    habit_custom: '',
    habit_description: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Moscow',
    accepted: false,
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const remaining = useMemo(() => 300 - form.habit_description.length, [form.habit_description])

  const update = (patch) => setForm((prev) => ({ ...prev, ...patch }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')

    if (!form.accepted) {
      setError('Please accept policy terms.')
      return
    }

    try {
      setLoading(true)
      await request('/onboarding/submit', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      onDone()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <form className="modal" onSubmit={submit}>
        <h2>Welcome</h2>
        <p>Tell us your habit goal to build a 3-4 month plan.</p>

        <label>
          Full name
          <input
            value={form.full_name}
            onChange={(e) => update({ full_name: e.target.value })}
            minLength={2}
            maxLength={255}
            required
          />
        </label>

        <label>
          Goal type
          <select value={form.goal_type} onChange={(e) => update({ goal_type: e.target.value })}>
            <option value="build">Build good habit</option>
            <option value="quit">Quit bad habit</option>
            <option value="both">Both</option>
          </select>
        </label>

        <label>
          Category
          <select value={form.habit_category} onChange={(e) => update({ habit_category: e.target.value })}>
            {CATEGORIES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        {form.habit_category === 'other' && (
          <label>
            Custom category
            <input
              value={form.habit_custom}
              onChange={(e) => update({ habit_custom: e.target.value })}
              maxLength={80}
            />
          </label>
        )}

        <label>
          Describe your habit
          <textarea
            value={form.habit_description}
            onChange={(e) => update({ habit_description: e.target.value })}
            maxLength={300}
            required
          />
          <span className="hint">{remaining} chars left</span>
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.accepted}
            onChange={(e) => update({ accepted: e.target.checked })}
          />
          I accept policy and data processing terms.
        </label>

        {error && <div className="error">{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Continue'}
        </button>
      </form>
    </div>
  )
}
