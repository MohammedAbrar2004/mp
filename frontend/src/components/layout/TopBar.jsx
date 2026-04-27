import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle, ScrollText } from 'lucide-react';
import { getSyncStatus, getConnectorLogs } from '../../api/client';

const SECTION_TITLES = {
  query: 'Query Interface',
  memory: 'Memory Browser',
  ingest: 'Manual Ingest',
  relationships: 'Relationships',
  connectors: 'Connectors',
  settings: 'Settings',
};

const SOURCE_COLORS = {
  gmail: '#EA4335',
  whatsapp: '#25D366',
  calendar: '#4285F4',
  manual: '#00897B',
};

function formatRelative(isoString) {
  if (!isoString) return 'never';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function TopBar({ activeSection }) {
  const [syncStatus, setSyncStatus] = useState(null);
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);

  useEffect(() => {
    getSyncStatus().then(setSyncStatus).catch(() => {});
    const id = setInterval(() => {
      getSyncStatus().then(setSyncStatus).catch(() => {});
    }, 60000);
    return () => clearInterval(id);
  }, []);

  const handleLogsClick = async () => {
    setShowLogs((prev) => !prev);
    if (!showLogs) {
      setLogsLoading(true);
      try {
        // fetch recent logs across all connectors via system_logs (use 'echomind' as broad match)
        const data = await getConnectorLogs('', 30);
        setLogs(data.logs || []);
      } catch {
        setLogs([]);
      } finally {
        setLogsLoading(false);
      }
    }
  };

  const failedCount = syncStatus?.failed_jobs_count ?? 0;
  const syncMap = syncStatus?.last_sync_per_source ?? {};

  const latestSync = Object.values(syncMap)
    .filter(Boolean)
    .sort((a, b) => new Date(b) - new Date(a))[0];

  return (
    <div className="flex flex-col">
      <div className="h-[52px] flex items-center justify-between px-5 bg-echo-surface border-b border-echo-border">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold text-echo-bright tracking-wide">
            {SECTION_TITLES[activeSection] || 'EchoMind'}
          </h1>
        </div>

        <div className="flex items-center gap-5 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="status-dot green" />
            <span className="text-echo-muted font-mono">Scheduler</span>
          </div>

          {/* Last sync with per-source tooltip */}
          <div className="flex items-center gap-1.5 group relative cursor-default">
            <Clock size={12} className="text-echo-muted" />
            <span className="text-echo-muted font-mono">
              {latestSync ? formatRelative(latestSync) : '—'}
            </span>
            <div className="absolute top-full right-0 mt-2 hidden group-hover:block z-50">
              <div className="bg-echo-panel border border-echo-border p-3 text-xs font-mono space-y-1 min-w-[180px]" style={{ borderRadius: '2px' }}>
                <div className="text-echo-bright text-[10px] uppercase tracking-wider mb-2">Last Sync Per Source</div>
                {Object.keys(syncMap).length === 0 ? (
                  <div className="text-echo-muted/60">No syncs recorded yet</div>
                ) : (
                  Object.entries(syncMap).map(([name, ts]) => (
                    <div key={name} className="flex justify-between">
                      <span style={{ color: SOURCE_COLORS[name] || '#aaa' }}>{name.charAt(0).toUpperCase() + name.slice(1)}</span>
                      <span className="text-echo-muted">{formatRelative(ts)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Failed jobs */}
          <div className="flex items-center gap-1.5">
            <AlertTriangle size={12} className={failedCount > 0 ? 'text-amber-400' : 'text-echo-muted'} />
            <span className={`font-mono font-medium ${failedCount > 0 ? 'text-amber-400' : 'text-echo-muted'}`}>
              {failedCount}
            </span>
          </div>

          {/* Logs button */}
          <button
            onClick={handleLogsClick}
            className={`flex items-center gap-1.5 transition-colors ${showLogs ? 'text-cyan-glow' : 'text-echo-muted hover:text-echo-text'}`}
          >
            <ScrollText size={12} />
            <span className="font-mono">Logs</span>
          </button>

          {/* EchoMind brand badge */}
          <div className="group relative cursor-default">
            <div className="flex items-center gap-1.5 px-2 py-1 bg-cyan-glow/10 border border-cyan-glow/25" style={{ borderRadius: '2px' }}>
              <span className="text-[10px] font-bold font-mono text-cyan-glow tracking-widest">EM</span>
            </div>
            <div className="absolute top-full right-0 mt-2 hidden group-hover:block z-50">
              <div className="bg-echo-panel border border-echo-border p-3 text-xs space-y-1.5 w-[220px]" style={{ borderRadius: '2px' }}>
                <div className="text-echo-bright font-semibold">EchoMind</div>
                <p className="text-echo-muted leading-relaxed">
                  Your personal semantic memory layer — ingests messages, emails, and notes, then lets you query your own context with AI.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Inline logs panel */}
      {showLogs && (
        <div className="border-b border-echo-border bg-echo-bg px-5 py-3 font-mono text-xs max-h-48 overflow-y-auto">
          {logsLoading ? (
            <span className="text-echo-muted/60">Loading logs...</span>
          ) : logs.length === 0 ? (
            <span className="text-echo-muted/60">No recent logs.</span>
          ) : (
            <div className="space-y-0.5">
              {logs.map((log, i) => (
                <div key={i} className={`leading-relaxed ${log.level === 'error' || log.level === 'critical' ? 'text-red-400' : log.level === 'warning' ? 'text-amber-400' : 'text-echo-muted'}`}>
                  <span className="text-echo-muted/50 mr-2">{log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}</span>
                  <span className="uppercase mr-2 text-[10px]">{log.level}</span>
                  <span className="text-echo-muted/70 mr-2">[{log.component}]</span>
                  {log.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
