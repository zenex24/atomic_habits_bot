const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

let accessToken = localStorage.getItem('atomic_access_token') || ''

function setToken(token) {
  accessToken = token
  localStorage.setItem('atomic_access_token', token)
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // no-op
    }
    throw new Error(detail)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export async function loginWithTelegram(initData) {
  const data = await request('/auth/telegram-login', {
    method: 'POST',
    body: JSON.stringify({ init_data: initData }),
  })
  setToken(data.access_token)
  return data
}

export async function devLogin(telegramId = 1000001) {
  const data = await request('/auth/dev-login', {
    method: 'POST',
    body: JSON.stringify({ telegram_id: telegramId, first_name: 'Local User' }),
  })
  setToken(data.access_token)
  return data
}

export { API_URL, request, setToken }
