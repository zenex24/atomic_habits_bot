import { useEffect, useState } from 'react'

import { devLogin, loginWithTelegram, request } from './api'
import { OnboardingModal } from './components/OnboardingModal'
import { TabBar } from './components/TabBar'
import { getInitData, initTelegram } from './telegram'
import { ChallengesPage } from './pages/ChallengesPage'
import { ChatPage } from './pages/ChatPage'
import { HomePage } from './pages/HomePage'
import { PlanPage } from './pages/PlanPage'
import { ProfilePage } from './pages/ProfilePage'

export default function App() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('home')

  const [profile, setProfile] = useState(null)
  const [plan, setPlan] = useState(null)
  const [messages, setMessages] = useState([])
  const [challenges, setChallenges] = useState([])

  const onboardingCompleted = Boolean(profile?.goal_type)

  const bootstrap = async () => {
    setError('')
    try {
      initTelegram()
      const initData = getInitData()
      if (initData) {
        await loginWithTelegram(initData)
      } else {
        await devLogin()
      }

      const [profileData, planData, chatData, challengeData] = await Promise.all([
        request('/profile/me'),
        request('/plan/current'),
        request('/chat/history').catch(() => []),
        request('/challenges').catch(() => []),
      ])

      setProfile(profileData)
      setPlan(planData)
      setMessages(chatData || [])
      setChallenges(challengeData || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    bootstrap()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const reloadProfile = async () => {
    const fresh = await request('/profile/me')
    setProfile(fresh)
  }

  let page = <HomePage profile={profile} plan={plan} />

  if (activeTab === 'chat') {
    page = <ChatPage messages={messages} onMessages={setMessages} />
  } else if (activeTab === 'plan') {
    page = <PlanPage plan={plan} onPlan={setPlan} />
  } else if (activeTab === 'challenges') {
    page = <ChallengesPage challenges={challenges} onChallenges={setChallenges} />
  } else if (activeTab === 'profile') {
    page = <ProfilePage profile={profile} onProfile={setProfile} />
  }

  if (loading) {
    return <div className="screen-center">Loading...</div>
  }

  if (error) {
    return (
      <div className="screen-center">
        <p className="error">{error}</p>
        <button onClick={bootstrap}>Retry</button>
      </div>
    )
  }

  return (
    <div className="app-shell">
      {!onboardingCompleted && <OnboardingModal onDone={reloadProfile} />}
      <main>{page}</main>
      <TabBar activeTab={activeTab} onChange={setActiveTab} />
    </div>
  )
}
