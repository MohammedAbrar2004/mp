import React, { useState, useEffect, useRef, useCallback } from 'react';
import { SlidersHorizontal, ChevronLeft, ChevronRight, Eye, X, Search, Loader2 } from 'lucide-react';
import { getMemoryChunks, getChunkDetail } from '../../api/client';
import SourceIcon from '../shared/SourceIcon';
import { SourceBadge } from '../shared/Badge';
import SalienceBar from '../shared/SalienceBar';
import DetailPanel from '../layout/DetailPanel';

const SOURCES = ['whatsapp', 'gmail', 'calendar', 'manual'];
const SOURCE_LABELS = { whatsapp: 'WhatsApp', gmail: 'Gmail', calendar: 'Calendar', manual: 'Manual' };
const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
  { value: 'salience', label: 'Highest Salience' },
];

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

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

export default function MemoryBrowser() {
  const [selectedSources, setSelectedSources] = useState(new Set());
  const [salienceMin, setSalienceMin] = useState(0);
  const [sortBy, setSortBy] = useState('newest');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [chunks, setChunks] = useState([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [detailChunk, setDetailChunk] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const searchDebounce = useRef(null);
  const perPage = 6;

  const fetchChunks = useCallback(async (params) => {
    setIsLoading(true);
    try {
      const data = await getMemoryChunks(params);
      setChunks(data.chunks || []);
      setTotal(data.total || 0);
    } catch {
      setChunks([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const connector_source = selectedSources.size === 1 ? [...selectedSources][0] : '';
    fetchChunks({
      search: searchQuery,
      connector_source,
      salience_min: salienceMin,
      salience_max: 1,
      sort: sortBy,
      page,
      per_page: perPage,
    });
  }, [selectedSources, salienceMin, sortBy, page, fetchChunks]);

  const handleSearchChange = (val) => {
    setSearchQuery(val);
    clearTimeout(searchDebounce.current);
    searchDebounce.current = setTimeout(() => {
      setPage(1);
      const connector_source = selectedSources.size === 1 ? [...selectedSources][0] : '';
      fetchChunks({ search: val, connector_source, salience_min: salienceMin, salience_max: 1, sort: sortBy, page: 1, per_page: perPage });
    }, 300);
  };

  const toggleSource = (src) => {
    setSelectedSources((prev) => {
      const next = new Set(prev);
      if (next.has(src)) {
        next.delete(src);
      } else {
        next.clear();
        next.add(src);
      }
      return next;
    });
    setPage(1);
  };

  const openDetail = async (chunk) => {
    setDetailChunk(chunk);
    setDetailLoading(true);
    try {
      const full = await getChunkDetail(chunk.memory_chunk_id);
      setDetailChunk(full);
    } catch {
      // keep the summary data
    } finally {
      setDetailLoading(false);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Search bar */}
      <div className="px-4 pt-4 pb-0">
        <div className="relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-echo-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search memories..."
            className="w-full pl-9 pr-9 py-2 bg-echo-bg border border-echo-border text-echo-text text-sm placeholder:text-echo-muted/50 focus:outline-none glow-input transition-all font-sans"
            style={{ borderRadius: '2px' }}
          />
          {searchQuery && (
            <button
              onClick={() => handleSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-echo-muted hover:text-echo-text transition-colors"
            >
              <X size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="p-4 border-b border-echo-border space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={14} className="text-echo-muted" />
            <span className="text-xs font-medium text-echo-muted uppercase tracking-wider">Filters</span>
          </div>
          <span className="text-xs font-mono text-echo-muted">{total} chunks</span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] text-echo-muted uppercase tracking-wider mr-1">Source</span>
          {SOURCES.map((src) => (
            <button
              key={src}
              onClick={() => toggleSource(src)}
              className={`tag-chip transition-all duration-150 cursor-pointer ${
                selectedSources.has(src) ? 'opacity-100' : 'opacity-30 hover:opacity-50'
              }`}
              style={{
                background: selectedSources.has(src) ? `var(--source-${src}-bg, rgba(136,146,168,0.15))` : 'transparent',
                border: '1px solid rgba(136,146,168,0.2)',
              }}
            >
              <SourceIcon source={src} size={11} className="mr-1" />
              {SOURCE_LABELS[src]}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-echo-muted uppercase tracking-wider">Sort</span>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
              className="bg-echo-bg border border-echo-border text-echo-text text-xs px-2 py-1 focus:outline-none focus:border-cyan-glow/40"
              style={{ borderRadius: '2px' }}
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-echo-muted uppercase tracking-wider">Salience ≥</span>
            <input
              type="range" min="0" max="1" step="0.05"
              value={salienceMin}
              onChange={(e) => { setSalienceMin(parseFloat(e.target.value)); setPage(1); }}
              className="w-24 accent-cyan-500"
            />
            <span className="text-xs font-mono text-echo-muted w-8">{salienceMin.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Cards grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 size={20} className="animate-spin text-echo-muted" />
          </div>
        ) : chunks.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-echo-muted/50">No memories found. Try adjusting filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {chunks.map((chunk) => (
              <div
                key={chunk.memory_chunk_id}
                className="glass-card p-4 hover-lift cursor-pointer group"
                style={{ borderRadius: '2px' }}
                onClick={() => openDetail(chunk)}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <SourceIcon source={chunk.connector_source} size={14} />
                    <SourceBadge source={chunk.connector_source} />
                  </div>
                  <span className="text-[10px] font-mono text-echo-muted">{formatRelativeTime(chunk.timestamp)}</span>
                </div>

                {chunk.title && (
                  <h4 className="text-xs font-semibold text-echo-bright mb-2">{chunk.title}</h4>
                )}

                <p className="text-xs text-echo-muted leading-relaxed line-clamp-3 mb-3">
                  {chunk.summary || ''}
                </p>

                <div className="flex items-center justify-between">
                  <div className="w-24">
                    <SalienceBar score={chunk.refined_salience ?? 0} showLabel />
                  </div>
                  <button className="opacity-0 group-hover:opacity-100 transition-opacity text-[10px] text-cyan-glow flex items-center gap-1">
                    <Eye size={11} />
                    View
                  </button>
                </div>

                {(chunk.keywords || []).length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {chunk.keywords.slice(0, 3).map((kw) => (
                      <span key={kw} className="text-[10px] font-mono text-echo-muted bg-echo-bg px-1.5 py-0.5" style={{ borderRadius: '2px' }}>
                        #{kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 mt-6 pb-4">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="p-1.5 text-echo-muted hover:text-echo-text disabled:opacity-30 transition-colors">
              <ChevronLeft size={16} />
            </button>
            <span className="text-xs font-mono text-echo-muted">{page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="p-1.5 text-echo-muted hover:text-echo-text disabled:opacity-30 transition-colors">
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Detail Panel */}
      <DetailPanel isOpen={!!detailChunk} onClose={() => setDetailChunk(null)} title="Memory Chunk Detail">
        {detailChunk && (
          <div className="space-y-5">
            {detailLoading && (
              <div className="flex items-center gap-2 text-xs text-echo-muted">
                <Loader2 size={12} className="animate-spin" /> Loading details...
              </div>
            )}

            <div className="flex items-center gap-2">
              <SourceIcon source={detailChunk.connector_source} size={16} />
              <SourceBadge source={detailChunk.connector_source} />
              <span className="text-xs font-mono text-echo-muted ml-auto">
                {formatDate(detailChunk.timestamp)} · {formatTime(detailChunk.timestamp)}
              </span>
            </div>

            {detailChunk.title && (
              <h3 className="text-base font-semibold text-echo-bright">{detailChunk.title}</h3>
            )}

            <div className="p-4 bg-echo-bg border border-echo-border" style={{ borderRadius: '2px' }}>
              <p className="text-sm text-echo-text leading-relaxed whitespace-pre-wrap">
                {detailChunk.raw_content || detailChunk.summary || ''}
              </p>
            </div>

            <div>
              <span className="text-[10px] text-echo-muted uppercase tracking-wider">Salience</span>
              <div className="mt-1">
                <SalienceBar score={detailChunk.refined_salience ?? 0} showLabel />
              </div>
            </div>

            {(detailChunk.entities || []).length > 0 && (
              <div>
                <span className="text-[10px] text-echo-muted uppercase tracking-wider">Entities</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {detailChunk.entities.map((ent) => (
                    <span key={ent.name} className="tag-chip bg-cyan-glow/10 text-cyan-glow border border-cyan-glow/20">
                      {ent.name}
                      <span className="text-echo-muted ml-1 text-[9px]">{ent.entity_type}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {(detailChunk.keywords || []).length > 0 && (
              <div>
                <span className="text-[10px] text-echo-muted uppercase tracking-wider">Keywords</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {detailChunk.keywords.map((kw) => (
                    <span key={kw} className="text-xs font-mono text-echo-muted bg-echo-hover px-2 py-0.5" style={{ borderRadius: '2px' }}>
                      #{kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 text-xs text-echo-muted font-mono">
              <span>ID: {detailChunk.memory_chunk_id}</span>
              <span>·</span>
              <span>Type: {detailChunk.content_type}</span>
            </div>
          </div>
        )}
      </DetailPanel>
    </div>
  );
}
