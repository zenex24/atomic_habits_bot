import { useState } from 'react'

import { request } from '../api'

export function ChatPage({ messages, onMessages }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const send = async (event) => {
    event.preventDefault()
    if (!text.trim()) return

    setLoading(true)
    setError('')

    try {
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
      }
      onMessages((prev) => [...prev, userMessage])

      const data = await request('/chat/messages', {
        method: 'POST',
        body: JSON.stringify({ text }),
      })

      onMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.answer,
          created_at: new Date().toISOString(),
        },
      ])
      setText('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page">
      <h1>Mentor Chat</h1>
      <div className="chat-box">
        {messages.length === 0 && <p className="hint">Ask your mentor how to improve your habit system.</p>}
        {messages.map((message) => (
          <div key={message.id} className={message.role === 'assistant' ? 'bubble assistant' : 'bubble user'}>
            {message.content}
          </div>
        ))}
      </div>

      <form className="chat-form" onSubmit={send}>
        <textarea
          placeholder="Type your message"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={1200}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}
    </section>
  )
}
