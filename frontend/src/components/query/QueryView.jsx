import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Mic, MicOff, Clock, Sparkles, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { postQuery, postVoiceQuery, getQueryHistory } from '../../api/client';
import SourceIcon from '../shared/SourceIcon';
import { SourceBadge, ModelBadge } from '../shared/Badge';
import SalienceBar from '../shared/SalienceBar';

function formatRelativeTime(isoString) {
  if (!isoString) return '';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function QueryView() {
  const [query, setQuery] = useState('');
  const [activeQuery, setActiveQuery] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(true);
  const [error, setError] = useState('');
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const loadHistory = useCallback(() => {
    getQueryHistory(20, 0).then((data) => setHistory(data.queries || [])).catch(() => {});
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    setIsLoading(true);
    setError('');
    try {
      const result = await postQuery(query.trim());
      setActiveQuery(result);
      setQuery('');
      loadHistory();
    } catch (err) {
      setError('Failed to submit query. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      return;
    }

    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError('Microphone access denied.');
      return;
    }

    audioChunksRef.current = [];
    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      setIsRecording(false);
      setIsLoading(true);
      setError('');
      try {
        const result = await postVoiceQuery(blob);
        setActiveQuery(result);
        setQuery('');
        loadHistory();
      } catch {
        setError('Voice query failed. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    recorder.start();
    setIsRecording(true);
  };

  const loadQueryFromHistory = (q) => {
    setActiveQuery(q);
    setQuery('');
    setError('');
  };

  const responseSecs = activeQuery?.response_time_ms
    ? (activeQuery.response_time_ms / 1000).toFixed(1)
    : null;

  return (
    <div className="h-full flex">
      {/* Query History — left column */}
      <div className="w-[260px] flex-shrink-0 border-r border-echo-border p-4 overflow-y-auto">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={14} className="text-echo-muted" />
          <span className="text-xs font-medium text-echo-muted uppercase tracking-wider">Recent Queries</span>
        </div>
        <div className="space-y-1">
          {history.length === 0 && (
            <p className="text-xs text-echo-muted/50 text-center py-4">No queries yet</p>
          )}
          {history.map((q) => (
            <button
              key={q.query_id}
              onClick={() => loadQueryFromHistory(q)}
              className={`w-full text-left p-3 transition-all duration-150 ${
                activeQuery?.query_id === q.query_id
                  ? 'bg-cyan-glow/8 border border-cyan-glow/20'
                  : 'border border-transparent hover:bg-echo-hover'
              }`}
              style={{ borderRadius: '2px' }}
            >
              <p className="text-xs text-echo-text leading-relaxed line-clamp-2">{q.query}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-[10px] font-mono text-echo-muted">{formatRelativeTime(q.created_at)}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main query area */}
      <div className="flex-1 flex flex-col items-center overflow-y-auto">
        <div className="w-full max-w-2xl pt-16 px-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-echo-bright mb-2">
              What do you want to recall?
            </h2>
            <p className="text-sm text-echo-muted">
              Query your memory across all connected sources
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask anything about your data..."
                className="w-full pl-4 pr-24 py-4 bg-echo-bg border border-echo-border text-echo-text text-sm placeholder:text-echo-muted/50 focus:outline-none glow-input transition-all font-sans"
                style={{ borderRadius: '2px' }}
              />

              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button
                  type="button"
                  onClick={toggleRecording}
                  className={`p-2 transition-colors ${isRecording ? 'text-red-400 animate-pulse' : 'text-echo-muted hover:text-echo-text'}`}
                  title={isRecording ? 'Stop recording' : 'Voice input'}
                >
                  {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
                </button>
                <button
                  type="submit"
                  disabled={!query.trim() || isLoading}
                  className="p-2 text-cyan-glow hover:text-cyan-400 transition-colors disabled:opacity-30"
                >
                  {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <p className="mt-2 text-xs text-red-400 font-mono">{error}</p>
            )}
          </form>
        </div>

        {activeQuery && (
          <div className="w-full max-w-2xl px-6 py-8 animate-fade-in">
            <div className="flex items-start gap-3 mb-5">
              <div className="w-7 h-7 flex items-center justify-center bg-echo-hover border border-echo-border flex-shrink-0" style={{ borderRadius: '2px' }}>
                <span className="text-xs font-mono text-echo-muted">Q</span>
              </div>
              <p className="text-sm text-echo-text pt-1">{activeQuery.query}</p>
            </div>

            <div className="glass-card p-5" style={{ borderRadius: '2px' }}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-7 h-7 flex items-center justify-center bg-cyan-glow/10 flex-shrink-0" style={{ borderRadius: '2px' }}>
                  <Sparkles size={14} className="text-cyan-glow" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-echo-muted px-1.5 py-0.5 border border-echo-border">AI</span>
                  {responseSecs && (
                    <span className="text-[10px] font-mono text-echo-muted">{responseSecs}s</span>
                  )}
                </div>
              </div>

              <div className="text-sm text-echo-text leading-relaxed whitespace-pre-wrap">
                {(activeQuery.answer || '').split('**').map((part, i) =>
                  i % 2 === 1
                    ? <strong key={i} className="text-echo-bright font-semibold">{part}</strong>
                    : <span key={i}>{part}</span>
                )}
              </div>

              {/* Sources */}
              <div className="mt-5 pt-4 border-t border-echo-border">
                <button
                  onClick={() => setSourcesExpanded(!sourcesExpanded)}
                  className="flex items-center gap-2 text-xs text-echo-muted hover:text-echo-text transition-colors mb-3"
                >
                  {sourcesExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  <span className="font-medium uppercase tracking-wider">
                    Sources ({(activeQuery.sources || []).length})
                  </span>
                </button>

                {sourcesExpanded && (activeQuery.sources || []).length > 0 && (
                  <div className="space-y-2 animate-fade-in">
                    {activeQuery.sources.map((chunk, i) => (
                      <div
                        key={chunk.memory_chunk_id || i}
                        className="flex items-start gap-3 p-3 bg-echo-bg border border-echo-border hover:border-echo-muted/30 transition-colors"
                        style={{ borderRadius: '2px' }}
                      >
                        <SourceIcon source={chunk.connector_source} size={14} className="mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1.5">
                            <SourceBadge source={chunk.connector_source} />
                            <span className="text-[10px] font-mono text-echo-muted">
                              {formatRelativeTime(chunk.timestamp)}
                            </span>
                          </div>
                          <p className="text-xs text-echo-muted leading-relaxed line-clamp-2">
                            {chunk.summary || chunk.title || ''}
                          </p>
                          {chunk.refined_salience != null && (
                            <div className="mt-2 w-32">
                              <SalienceBar score={chunk.refined_salience} showLabel />
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {sourcesExpanded && (activeQuery.sources || []).length === 0 && (
                  <p className="text-xs text-echo-muted/50 italic">No sources retrieved for this query.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
