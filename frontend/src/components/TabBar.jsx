const TABS = [
  { id: 'home', label: 'Home' },
  { id: 'chat', label: 'Chat' },
  { id: 'plan', label: 'Plan' },
  { id: 'challenges', label: 'Challenges' },
  { id: 'profile', label: 'Profile' },
]

export function TabBar({ activeTab, onChange }) {
  return (
    <nav className="tabbar">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={activeTab === tab.id ? 'tab-item active' : 'tab-item'}
          onClick={() => onChange(tab.id)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
