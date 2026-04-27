import React, { useState } from 'react';
import Sidebar from './components/layout/Sidebar';
import TopBar from './components/layout/TopBar';
import QueryView from './components/query/QueryView';
import MemoryBrowser from './components/memory/MemoryBrowser';
import IngestView from './components/ingest/IngestView';
import RelationshipsView from './components/relationships/RelationshipsView';
import ConnectorsView from './components/connectors/ConnectorsView';
import SettingsView from './components/settings/SettingsView';

const SECTIONS = {
  query: QueryView,
  memory: MemoryBrowser,
  ingest: IngestView,
  relationships: RelationshipsView,
  connectors: ConnectorsView,
  settings: SettingsView,
};

export default function App() {
  const [activeSection, setActiveSection] = useState('query');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [prevSection, setPrevSection] = useState(null);

  const handleNavigate = (section) => {
    if (section === activeSection) return;
    setPrevSection(activeSection);
    setActiveSection(section);
  };

  const ActiveComponent = SECTIONS[activeSection];

  return (
    <div className="h-screen flex bg-echo-bg">
      {/* Sidebar */}
      <Sidebar
        activeSection={activeSection}
        onNavigate={handleNavigate}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <TopBar activeSection={activeSection} />

        {/* Content area */}
        <main className="flex-1 overflow-hidden dot-grid">
          <div key={activeSection} className="h-full animate-fade-in">
            <ActiveComponent />
          </div>
        </main>
      </div>
    </div>
  );
}
