const tabs = [
  { key: "home", label: "Главная" },
  { key: "chat", label: "Чат" },
  { key: "plan", label: "План" },
  { key: "challenges", label: "Челленджи" },
  { key: "profile", label: "Профиль" },
];

export default function TabBar({ activeTab, setActiveTab }) {
  return (
    <nav className="tabbar">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          className={`tabbar-item ${activeTab === tab.key ? "active" : ""}`}
          onClick={() => setActiveTab(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
