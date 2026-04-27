import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Pause, Play, KeyRound, ScrollText, Wifi, WifiOff, QrCode, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import {
  getConnectorStatus, getIngestionRuns, getConnectorLogs,
  syncConnector, pauseConnector, reauthWhatsapp, deleteGmailToken, deleteCalendarToken,
} from '../../api/client';
import SourceIcon from '../shared/SourceIcon';
import { StatusBadge } from '../shared/Badge';
import Modal from '../shared/Modal';

const SOURCE_COLORS = {
  gmail: '#EA4335',
  whatsapp: '#25D366',
  calendar: '#4285F4',
  manual: '#00897B',
};

function formatRelativeTime(iso) {
  if (!iso) return 'never';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function ConnectorsView() {
  const [connectorList, setConnectorList] = useState([]);
  const [runsList, setRunsList] = useState([]);
  const [showLogs, setShowLogs] = useState(null);
  const [logs, setLogs] = useState([]);
  const [showRunsTable, setShowRunsTable] = useState(true);
  const [syncing, setSyncing] = useState({});
  const [reauthMsg, setReauthMsg] = useState('');

  const fetchStatus = useCallback(() => {
    getConnectorStatus().then((d) => setConnectorList(d.connectors || [])).catch(() => {});
    getIngestionRuns('', 20).then((d) => setRunsList(d.runs || [])).catch(() => {});
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleSync = async (connector) => {
    setSyncing((s) => ({ ...s, [connector]: true }));
    try {
      await syncConnector(connector);
      setTimeout(fetchStatus, 3000);
    } catch { }
    finally { setSyncing((s) => ({ ...s, [connector]: false })); }
  };

  const handlePause = async (connector, currentlyActive) => {
    try {
      await pauseConnector(connector, !currentlyActive);
      setConnectorList((prev) => prev.map((c) => c.connector === connector ? { ...c, is_active: !currentlyActive, status: !currentlyActive ? 'active' : 'inactive' } : c));
    } catch { }
  };

  const handleReauth = async (connector) => {
    try {
      if (connector === 'whatsapp') {
        const res = await reauthWhatsapp();
        if (res.requires_qr) {
          setConnectorList((prev) => prev.map((c) => c.connector === 'whatsapp' ? { ...c, status: 'auth_required' } : c));
        }
      } else if (connector === 'gmail') {
        await deleteGmailToken();
        setReauthMsg('Gmail token deleted. Please restart the Gmail connector and complete OAuth in your browser.');
      } else if (connector === 'calendar') {
        await deleteCalendarToken();
        setReauthMsg('Calendar token deleted. Please restart the Calendar connector and complete OAuth in your browser.');
      }
    } catch (err) {
      setReauthMsg('Re-auth failed: ' + err.message);
    }
  };

  const handleShowLogs = async (connector) => {
    setShowLogs(connector);
    try {
      const data = await getConnectorLogs(connector, 50);
      setLogs(data.logs || []);
    } catch {
      setLogs([]);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        {reauthMsg && (
          <div className="mb-4 p-3 bg-amber-400/10 border border-amber-400/30 text-xs text-amber-300 font-mono" style={{ borderRadius: '2px' }}>
            {reauthMsg}
            <button onClick={() => setReauthMsg('')} className="ml-3 underline">dismiss</button>
          </div>
        )}

        <div className="grid grid-cols-3 gap-4 mb-6">
          {connectorList.map((conn) => (
            <div key={conn.connector} className="glass-card p-4 hover-lift" style={{ borderRadius: '2px', borderTop: `2px solid ${SOURCE_COLORS[conn.connector] || '#8892a8'}` }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <SourceIcon source={conn.connector} size={18} />
                  <span className="text-sm font-semibold text-echo-bright">{conn.name}</span>
                </div>
                <StatusBadge status={conn.status} />
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <span className="text-[10px] text-echo-muted uppercase tracking-wider block mb-0.5">Last Sync</span>
                  <span className="text-xs font-mono text-echo-text">{formatRelativeTime(conn.last_synced_at)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-echo-muted uppercase tracking-wider block mb-0.5">Chunks</span>
                  <span className="text-xs font-mono text-cyan-glow">{(conn.chunks_ingested || 0).toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-[10px] text-echo-muted uppercase tracking-wider block mb-0.5">Mode</span>
                  <span className="text-xs font-mono text-echo-text capitalize">{conn.mode}</span>
                </div>
              </div>

              {conn.connector === 'whatsapp' && conn.status === 'auth_required' && (
                <div className="mb-4 p-3 border border-amber-400/20 bg-amber-400/5" style={{ borderRadius: '2px' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <QrCode size={14} className="text-amber-400" />
                    <span className="text-xs text-amber-400 font-medium">QR Code Required</span>
                  </div>
                  <div className="w-24 h-24 bg-echo-bg border border-echo-border flex items-center justify-center mx-auto" style={{ borderRadius: '2px' }}>
                    <span className="text-[10px] text-echo-muted font-mono">Restart bridge to generate QR</span>
                  </div>
                  <p className="text-[10px] text-red-400 font-mono mt-2 text-center">Session expired. Re-authentication required.</p>
                </div>
              )}

              <div className="flex items-center gap-1 pt-3 border-t border-echo-border flex-wrap">
                {(conn.status === 'auth_required' || ['gmail', 'calendar', 'whatsapp'].includes(conn.connector)) && (
                  <button onClick={() => handleReauth(conn.connector)}
                    className="flex items-center gap-1 px-2 py-1 text-[10px] text-amber-400 hover:bg-amber-400/10 transition-colors" style={{ borderRadius: '2px' }}>
                    <KeyRound size={10} /> Re-auth
                  </button>
                )}
                <button onClick={() => handleSync(conn.connector)} disabled={syncing[conn.connector]}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] text-cyan-glow hover:bg-cyan-glow/10 transition-colors disabled:opacity-50" style={{ borderRadius: '2px' }}>
                  {syncing[conn.connector] ? <Loader2 size={10} className="animate-spin" /> : <RefreshCw size={10} />} Sync
                </button>
                <button onClick={() => handlePause(conn.connector, conn.is_active)}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] text-echo-muted hover:bg-echo-hover transition-colors" style={{ borderRadius: '2px' }}>
                  {conn.is_active ? <><Pause size={10} /> Pause</> : <><Play size={10} /> Resume</>}
                </button>
                <button onClick={() => handleShowLogs(conn.connector)}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] text-echo-muted hover:bg-echo-hover transition-colors" style={{ borderRadius: '2px' }}>
                  <ScrollText size={10} /> Logs
                </button>
              </div>
            </div>
          ))}

          {connectorList.length === 0 && (
            <div className="col-span-3 flex items-center justify-center h-32 text-echo-muted text-sm">
              <Loader2 size={16} className="animate-spin mr-2" /> Loading connectors...
            </div>
          )}
        </div>

        {/* Ingestion Runs Table */}
        <div className="mb-4">
          <button onClick={() => setShowRunsTable(!showRunsTable)} className="flex items-center gap-2 mb-3">
            {showRunsTable ? <ChevronUp size={14} className="text-echo-muted" /> : <ChevronDown size={14} className="text-echo-muted" />}
            <span className="text-xs font-semibold text-echo-bright uppercase tracking-wider">Ingestion Runs</span>
          </button>

          {showRunsTable && (
            <div className="border border-echo-border overflow-hidden" style={{ borderRadius: '2px' }}>
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-echo-panel">
                    <th className="text-left px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Timestamp</th>
                    <th className="text-left px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Connector</th>
                    <th className="text-left px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Chunks</th>
                    <th className="text-left px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Duration</th>
                    <th className="text-left px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {runsList.length === 0 ? (
                    <tr><td colSpan={5} className="px-3 py-4 text-center text-echo-muted/50 text-xs">No ingestion runs yet</td></tr>
                  ) : (
                    runsList.map((run) => (
                      <tr key={run.id} className="border-t border-echo-border hover:bg-echo-hover transition-colors">
                        <td className="px-3 py-2 font-mono text-echo-muted">{formatRelativeTime(run.timestamp)}</td>
                        <td className="px-3 py-2 text-echo-text capitalize">{run.connector}</td>
                        <td className="px-3 py-2 font-mono text-echo-text">{run.chunks}</td>
                        <td className="px-3 py-2 font-mono text-echo-muted">
                          {run.duration_ms != null ? `${(run.duration_ms / 1000).toFixed(1)}s` : '—'}
                        </td>
                        <td className="px-3 py-2">
                          <span className={`tag-chip ${run.status === 'success' ? 'bg-green-500/15 text-green-400' : run.status === 'running' ? 'bg-blue-500/15 text-blue-400' : 'bg-red-500/15 text-red-400'}`}>
                            {run.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Logs Modal */}
      <Modal isOpen={!!showLogs} onClose={() => setShowLogs(null)}
        title={`${showLogs ? showLogs.charAt(0).toUpperCase() + showLogs.slice(1) : ''} Connector Logs`} size="lg">
        <div className="bg-echo-bg border border-echo-border p-4 font-mono text-xs space-y-1 max-h-80 overflow-y-auto" style={{ borderRadius: '2px' }}>
          {logs.length === 0 ? (
            <p className="text-echo-muted/50 text-center">No logs found for this connector.</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className={`leading-relaxed ${log.level === 'error' || log.level === 'critical' ? 'text-red-400' : log.level === 'warning' ? 'text-amber-400' : 'text-echo-muted'}`}>
                <span className="text-echo-muted/50 mr-2">{log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}</span>
                <span className="uppercase mr-2">{log.level}</span>
                {log.message}
              </div>
            ))
          )}
        </div>
      </Modal>
    </div>
  );
}
