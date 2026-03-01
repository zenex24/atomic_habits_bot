import { useState } from "react";
import { apiRequest } from "../lib/api";

export default function ChatTab({ mentorMode }) {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Привет. Я помогу закрепить полезные привычки и убрать вредные." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setInput("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setLoading(true);

    try {
      const data = await apiRequest("/api/v1/chat/message", "POST", {
        message: userMessage,
        mentor_mode: mentorMode,
      });
      setMessages((prev) => [...prev, { role: "assistant", text: data.answer }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="tab-content chat-tab">
      <div className="chat-window">
        {messages.map((msg, idx) => (
          <div key={`${msg.role}-${idx}`} className={`bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
      </div>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Напиши вопрос наставнику"
          maxLength={600}
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? "..." : "Отправить"}
        </button>
      </div>
    </section>
  );
}
