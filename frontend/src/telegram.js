export function getTelegramWebApp() {
  if (typeof window === 'undefined') return null
  return window.Telegram?.WebApp || null
}

export function initTelegram() {
  const tg = getTelegramWebApp()
  if (!tg) return null

  tg.ready()
  tg.expand()
  return tg
}

export function getInitData() {
  const tg = getTelegramWebApp()
  if (!tg) return ''
  return tg.initData || ''
}
