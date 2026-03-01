import { useState } from 'react'

import { request } from '../api'

export function PlanPage({ plan, onPlan }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await request('/plan/generate', {
        method: 'POST',
        body: JSON.stringify({}),
      })
      onPlan(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const updateTask = async (taskId, status) => {
    try {
      const updated = await request(`/plan/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      })
      onPlan((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          tasks: prev.tasks.map((item) => (item.id === taskId ? { ...item, status: updated.status } : item)),
        }
      })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="page">
      <h1>Plan</h1>
      <button onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate 3-4 month plan'}
      </button>

      {error && <div className="error">{error}</div>}

      {!plan && <p className="hint">No active plan yet.</p>}

      {plan && (
        <div className="plan-list">
          {plan.tasks.map((task) => (
            <article className="card" key={task.id}>
              <h3>{task.title}</h3>
              <p>{task.description}</p>
              <small>
                Due: {task.due_date} | Status: {task.status}
              </small>
              <div className="inline-actions">
                <button onClick={() => updateTask(task.id, 'completed')}>Done</button>
                <button onClick={() => updateTask(task.id, 'missed')}>Missed</button>
                <button onClick={() => updateTask(task.id, 'not_started')}>Reset</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
