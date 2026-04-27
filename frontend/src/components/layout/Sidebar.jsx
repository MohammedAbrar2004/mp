import React from 'react';
import {
  Search, Brain, Database, PenTool, Network,
  Plug, Settings, ChevronLeft, ChevronRight, Zap
} from 'lucide-react';

const navItems = [
  { id: 'query', label: 'Query', icon: Search },
  { id: 'memory', label: 'Memory', icon: Database },
  { id: 'ingest', label: 'Ingest', icon: PenTool },
  { id: 'relationships', label: 'Relations', icon: Network },
  { id: 'connectors', label: 'Connectors', icon: Plug },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ activeSection, onNavigate, collapsed, onToggle }) {
  return (
    <div
      className={`h-full flex flex-col bg-echo-surface border-r border-echo-border transition-all duration-300 ${collapsed ? 'w-[56px]' : 'w-[200px]'
        }`}
    >
      {/* Logo area */}
      <div className="flex items-center gap-2.5 px-3 h-[52px] border-b border-echo-border">
        <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
          <Brain size={20} className="text-cyan-glow" style={{ filter: 'drop-shadow(0 0 6px rgba(0,229,204,0.4))' }} />
        </div>
        {!collapsed && (
          <div className="flex items-center gap-1.5 overflow-hidden">
            <span className="text-sm font-semibold text-echo-bright tracking-wide whitespace-nowrap">EchoMind</span>
            <Zap size={11} className="text-amber-400 flex-shrink-0" />
          </div>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map(({ id, label, icon: Icon }) => {
          const isActive = activeSection === id;
          return (
            <button
              key={id}
              id={`nav-${id}`}
              onClick={() => onNavigate(id)}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 text-left transition-all duration-150 group ${collapsed ? 'justify-center' : ''
                } ${isActive
                  ? 'bg-cyan-glow/8 text-cyan-glow'
                  : 'text-echo-muted hover:text-echo-text hover:bg-echo-hover'
                }`}
              style={{ borderRadius: '2px' }}
              title={collapsed ? label : undefined}
            >
              <Icon
                size={17}
                className={`flex-shrink-0 transition-colors duration-150 ${isActive ? 'text-cyan-glow' : 'text-echo-muted group-hover:text-echo-text'
                  }`}
                style={isActive ? { filter: 'drop-shadow(0 0 4px rgba(0,229,204,0.3))' } : {}}
              />
              {!collapsed && (
                <span className={`text-[13px] whitespace-nowrap ${isActive ? 'font-medium' : 'font-normal'}`}>
                  {label}
                </span>
              )}
              {isActive && (
                <div
                  className="absolute left-0 w-[2px] h-5 bg-cyan-glow"
                  style={{ boxShadow: '0 0 8px rgba(0,229,204,0.5)' }}
                />
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-10 border-t border-echo-border text-echo-muted hover:text-echo-text transition-colors"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </div>
  );
}
