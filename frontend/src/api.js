const LOCAL_API_URL = 'http://localhost:8000'

function resolveApiUrl() {
  const envUrl = import.meta.env.VITE_API_URL?.trim()
  if (envUrl) return envUrl

  if (typeof window === 'undefined') return LOCAL_API_URL

  const host = window.location.hostname
  if (host === 'localhost' || host === '127.0.0.1') {
    return LOCAL_API_URL
  }

  return ''
}

function safeStorageGet(key) {
  try {
    return window.localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

function safeStorageSet(key, value) {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // no-op
  }
}

const API_URL = resolveApiUrl()

let accessToken = safeStorageGet('atomic_access_token')

function setToken(token) {
  accessToken = token
  safeStorageSet('atomic_access_token', token)
}

function getDefaultDemoState() {
  return {
    profile: {
      telegram_id: 1000001,
      full_name: null,
      mentor_tone: 'friendly',
      goal_type: null,
      habit_category: null,
      habit_description: null,
      is_paid: true,
      stats: {
        streak_days: 0,
        completed_tasks: 0,
        total_points: 0,
        active_challenges: 0,
      },
    },
    plan: null,
    messages: [],
    challenges: [],
    reminder: null,
    next_task_id: 1,
    next_challenge_id: 1,
  }
}

function readDemoState() {
  try {
    const raw = window.localStorage.getItem('atomic_demo_state')
    if (!raw) return getDefaultDemoState()
    return { ...getDefaultDemoState(), ...JSON.parse(raw) }
  } catch {
    return getDefaultDemoState()
  }
}

function writeDemoState(state) {
  try {
    window.localStorage.setItem('atomic_demo_state', JSON.stringify(state))
  } catch {
    // no-op
  }
}

function parseBody(options) {
  try {
    return options?.body ? JSON.parse(options.body) : {}
  } catch {
    return {}
  }
}

function computeDemoStats(state) {
  const tasks = state.plan?.tasks || []
  const completed = tasks.filter((task) => task.status === 'completed')
  const totalPoints = completed.reduce((acc, task) => acc + (task.points || 0), 0)
  const activeChallenges = state.challenges.filter((item) => item.status === 'active').length
  state.profile.stats = {
    streak_days: Math.min(30, completed.length),
    completed_tasks: completed.length,
    total_points: totalPoints,
    active_challenges: activeChallenges,
  }
}

function generateDemoPlan(state) {
  const today = new Date()
  const endDate = new Date(today)
  endDate.setDate(today.getDate() + 119)
  const tasks = []

  for (let week = 0; week < 16; week += 1) {
    const due = new Date(today)
    due.setDate(today.getDate() + week * 7)
    tasks.push({
      id: state.next_task_id++,
      title: `Week ${week + 1}: Consistent habit action`,
      description: 'Do the smallest possible version daily and track consistency.',
      due_date: due.toISOString().slice(0, 10),
      status: 'not_started',
      points: 20,
    })
  }

  state.plan = {
    id: 1,
    start_date: today.toISOString().slice(0, 10),
    end_date: endDate.toISOString().slice(0, 10),
    status: 'active',
    tasks,
  }
}

function buildDemoAnswer(text, tone) {
  const tonePrefix =
    tone === 'strict'
      ? 'Focus on execution: '
      : tone === 'balanced'
      ? 'Practical approach: '
      : 'Friendly reminder: '
  return `${tonePrefix}start tiny today, repeat tomorrow, and stack this habit after an existing routine. You asked: "${text.slice(0, 120)}".`
}

async function mockRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const state = readDemoState()
  const body = parseBody(options)

  if (path === '/auth/telegram-login' && method === 'POST') {
    return { access_token: 'demo-token', token_type: 'bearer' }
  }

  if (path === '/auth/dev-login' && method === 'POST') {
    return { access_token: 'demo-token', token_type: 'bearer' }
  }

  if (path === '/onboarding/submit' && method === 'POST') {
    state.profile.full_name = body.full_name || state.profile.full_name
    state.profile.goal_type = body.goal_type || state.profile.goal_type
    state.profile.habit_category = body.habit_category || state.profile.habit_category
    state.profile.habit_description = body.habit_description || state.profile.habit_description
    writeDemoState(state)
    return { ok: true }
  }

  if (path === '/profile/me' && method === 'GET') {
    computeDemoStats(state)
    writeDemoState(state)
    return state.profile
  }

  if (path === '/plan/current' && method === 'GET') {
    return state.plan
  }

  if (path === '/plan/generate' && method === 'POST') {
    generateDemoPlan(state)
    writeDemoState(state)
    return state.plan
  }

  if (path.startsWith('/plan/tasks/') && method === 'PATCH') {
    const id = Number(path.split('/').pop())
    const task = state.plan?.tasks?.find((item) => item.id === id)
    if (!task) {
      throw new Error('Task not found')
    }
    task.status = body.status || task.status
    writeDemoState(state)
    return task
  }

  if (path === '/chat/history' && method === 'GET') {
    return state.messages
  }

  if (path === '/chat/messages' && method === 'POST') {
    const now = new Date().toISOString()
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: body.text || '',
      created_at: now,
    }
    const assistantMsg = {
      id: Date.now() + 1,
      role: 'assistant',
      content: buildDemoAnswer(body.text || '', state.profile.mentor_tone),
      created_at: now,
    }
    state.messages.push(userMsg, assistantMsg)
    writeDemoState(state)
    return {
      answer: assistantMsg.content,
      remaining_messages_today: 999,
      context_used: [],
    }
  }

  if (path === '/challenges' && method === 'GET') {
    return state.challenges
  }

  if (path === '/challenges' && method === 'POST') {
    const days = Number(body.duration_days || 21)
    const start = new Date()
    const end = new Date(start)
    end.setDate(start.getDate() + days - 1)
    const challenge = {
      id: state.next_challenge_id++,
      title: body.title || 'New challenge',
      description: body.description || null,
      duration_days: days,
      start_date: start.toISOString().slice(0, 10),
      end_date: end.toISOString().slice(0, 10),
      status: 'active',
      reward_points: 0,
      days: [],
    }
    state.challenges.unshift(challenge)
    writeDemoState(state)
    return challenge
  }

  if (path.startsWith('/challenges/') && path.endsWith('/checkin') && method === 'POST') {
    const id = Number(path.split('/')[2])
    const challenge = state.challenges.find((item) => item.id === id)
    if (!challenge) {
      throw new Error('Challenge not found')
    }
    if (body.status === 'completed') {
      challenge.reward_points += 10
    }
    writeDemoState(state)
    return challenge
  }

  if (path === '/profile/mentor-tone' && method === 'POST') {
    state.profile.mentor_tone = body.tone || state.profile.mentor_tone
    writeDemoState(state)
    return { ok: true }
  }

  if (path === '/profile/reminder' && method === 'GET') {
    return state.reminder
  }

  if (path === '/profile/reminder' && method === 'POST') {
    state.reminder = {
      id: 1,
      daily_time: body.daily_time || '09:00',
      text: body.text || 'Time to work on your habit plan.',
      enabled: Boolean(body.enabled),
    }
    writeDemoState(state)
    return state.reminder
  }

  if (path === '/billing/dev-activate' && method === 'POST') {
    state.profile.is_paid = true
    writeDemoState(state)
    return { ok: true }
  }

  throw new Error(`Demo mode: endpoint is not implemented (${method} ${path})`)
}

async function request(path, options = {}) {
  if (!API_URL) {
    return mockRequest(path, options)
  }

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
