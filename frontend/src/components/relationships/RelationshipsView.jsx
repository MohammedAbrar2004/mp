import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { getRelationEntities, getRelationGraph, updateEntityAbout } from '../../api/client';
import { TypeBadge } from '../shared/Badge';

const NODE_COLORS = {
  person:     '#00e5cc',
  project:    '#a78bfa',
  tool:       '#fbbf24',
  task:       '#f97316',
  technology: '#60a5fa',
  topic:      '#4ade80',
  concept:    '#f472b6',
  default:    '#8892a8',
};

const TYPE_FILTERS = [
  { id: 'all',     label: 'All' },
  { id: 'person',  label: 'People' },
  { id: 'project', label: 'Projects' },
  { id: 'tool',    label: 'Tools' },
  { id: 'task',    label: 'Tasks' },
];

function getNodeColor(type) {
  return NODE_COLORS[type] || NODE_COLORS.default;
}

function runForceSimulation(nodes, edges, width = 700, height = 480, iterations = 100) {
  if (nodes.length === 0) return {};

  const positions = {};
  const angle = (2 * Math.PI) / nodes.length;
  const radius = Math.min(width, height) * 0.35;
  nodes.forEach((n, i) => {
    positions[n.entity_id] = {
      x: width / 2 + radius * Math.cos(i * angle),
      y: height / 2 + radius * Math.sin(i * angle),
      vx: 0,
      vy: 0,
    };
  });

  for (let iter = 0; iter < iterations; iter++) {
    const cooling = 1 - iter / iterations;

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = positions[nodes[i].entity_id];
        const b = positions[nodes[j].entity_id];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (4000 / (dist * dist)) * cooling;
        a.vx -= (dx / dist) * force;
        a.vy -= (dy / dist) * force;
        b.vx += (dx / dist) * force;
        b.vy += (dy / dist) * force;
      }
    }

    edges.forEach((e) => {
      const a = positions[e.source_entity_id];
      const b = positions[e.target_entity_id];
      if (!a || !b) return;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const ideal = 160;
      const force = ((dist - ideal) / dist) * 0.12 * cooling;
      a.vx += dx * force;
      a.vy += dy * force;
      b.vx -= dx * force;
      b.vy -= dy * force;
    });

    nodes.forEach((n) => {
      const p = positions[n.entity_id];
      p.vx += (width / 2 - p.x) * 0.008 * cooling;
      p.vy += (height / 2 - p.y) * 0.008 * cooling;
    });

    nodes.forEach((n) => {
      const p = positions[n.entity_id];
      p.x = Math.max(50, Math.min(width - 50, p.x + p.vx));
      p.y = Math.max(50, Math.min(height - 50, p.y + p.vy));
      p.vx *= 0.6;
      p.vy *= 0.6;
    });
  }

  return positions;
}

export default function RelationshipsView() {
  const [entityList, setEntityList] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [typeFilter, setTypeFilter] = useState('all');
  const [minSharedEvents, setMinSharedEvents] = useState(1);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [entitySearch, setEntitySearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [hoveredEdge, setHoveredEdge] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [editingAbout, setEditingAbout] = useState(null);
  const [aboutDraft, setAboutDraft] = useState('');
  const aboutInputRef = useRef(null);
  const SVG_W = 780;
  const SVG_H = 500;

  useEffect(() => {
    getRelationEntities()
      .then((d) => setEntityList(d.entities || []))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    getRelationGraph({
      entity_id: selectedEntity || '',
      min_shared_events: minSharedEvents,
      type_filter: typeFilter,
    })
      .then((d) => {
        setNodes(d.nodes || []);
        setEdges(d.edges || []);
      })
      .catch(() => {
        setNodes([]);
        setEdges([]);
      });
  }, [selectedEntity, minSharedEvents, typeFilter]);

  const nodePositions = useMemo(
    () => runForceSimulation(nodes, edges, SVG_W, SVG_H),
    [nodes, edges]
  );

  const filteredEntityList = useMemo(() => {
    const q = entitySearch.toLowerCase();
    return entityList.filter((e) => !q || e.name.toLowerCase().includes(q));
  }, [entityList, entitySearch]);

  const hoveredNodeData = useMemo(() => {
    if (!hoveredNode) return null;
    return nodes.find((n) => n.entity_id === hoveredNode)
      || entityList.find((e) => e.entity_id === hoveredNode);
  }, [hoveredNode, nodes, entityList]);

  const handleEntityClick = (entity) => {
    const isSame = selectedEntity === entity.entity_id;
    setSelectedEntity(isSame ? null : entity.entity_id);
    if (!isSame) {
      setEditingAbout(entity.entity_id);
      setAboutDraft(entity.about || '');
      setTimeout(() => aboutInputRef.current?.focus(), 50);
    } else {
      setEditingAbout(null);
    }
  };

  const handleAboutSave = async (entityId) => {
    const trimmed = aboutDraft.trim();
    try {
      await updateEntityAbout(entityId, trimmed);
      setEntityList((prev) =>
        prev.map((e) => (e.entity_id === entityId ? { ...e, about: trimmed || null } : e))
      );
    } catch {}
    setEditingAbout(null);
  };

  const handleAboutKeyDown = (e, entityId) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAboutSave(entityId);
    }
    if (e.key === 'Escape') setEditingAbout(null);
  };

  return (
    <div className="h-full flex overflow-hidden">
      {/* Left: entity list */}
      <div className="w-[240px] flex-shrink-0 border-r border-echo-border flex flex-col">
        <div className="p-3 border-b border-echo-border">
          <div className="relative">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-echo-muted" />
            <input
              type="text"
              value={entitySearch}
              onChange={(e) => setEntitySearch(e.target.value)}
              placeholder="Search entities..."
              className="w-full pl-7 pr-3 py-1.5 bg-echo-bg border border-echo-border text-xs text-echo-text focus:outline-none glow-input"
              style={{ borderRadius: '2px' }}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="flex items-center justify-center h-20">
              <Loader2 size={16} className="animate-spin text-echo-muted" />
            </div>
          ) : filteredEntityList.length === 0 ? (
            <p className="text-xs text-echo-muted/50 text-center py-4">No entities with mention count &gt; 7</p>
          ) : (
            filteredEntityList.map((e) => {
              const isSelected = selectedEntity === e.entity_id;
              const isEditing = editingAbout === e.entity_id;
              return (
                <div key={e.entity_id} className="mb-0.5">
                  <button
                    onClick={() => handleEntityClick(e)}
                    className={`w-full flex items-center gap-2 px-2 py-2 text-left transition-all ${
                      isSelected
                        ? 'bg-cyan-glow/8 border border-cyan-glow/20'
                        : 'hover:bg-echo-hover border border-transparent'
                    }`}
                    style={{ borderRadius: '2px' }}
                  >
                    <div
                      className="w-6 h-6 flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                      style={{
                        background: `${getNodeColor(e.entity_type)}20`,
                        color: getNodeColor(e.entity_type),
                        borderRadius: '2px',
                      }}
                    >
                      {e.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-echo-text truncate">{e.name}</p>
                      <div className="flex items-center gap-1 mt-0.5">
                        <TypeBadge type={e.entity_type} />
                        <span className="text-[10px] font-mono text-echo-muted">{e.mention_count}</span>
                      </div>
                      {e.about && !isEditing && (
                        <p className="text-[10px] text-echo-muted/60 mt-0.5 truncate italic">{e.about}</p>
                      )}
                    </div>
                  </button>
                  {isEditing && (
                    <div className="px-2 pb-2">
                      <textarea
                        ref={aboutInputRef}
                        value={aboutDraft}
                        onChange={(ev) => setAboutDraft(ev.target.value)}
                        onBlur={() => handleAboutSave(e.entity_id)}
                        onKeyDown={(ev) => handleAboutKeyDown(ev, e.entity_id)}
                        maxLength={120}
                        rows={2}
                        placeholder="Brief description (≤20 words)..."
                        className="w-full px-2 py-1.5 bg-echo-bg border border-cyan-glow/30 text-[11px] text-echo-text placeholder:text-echo-muted/40 focus:outline-none resize-none"
                        style={{ borderRadius: '2px' }}
                      />
                      <p className="text-[9px] text-echo-muted/50 mt-0.5">Enter to save · Esc to cancel</p>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right: graph */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <svg
          width="100%" height="100%"
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          className="flex-1"
          onMouseLeave={() => { setHoveredNode(null); setHoveredEdge(null); }}
        >
          <defs>
            <marker id="arrowhead" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto">
              <polygon points="0 0, 6 2, 0 4" fill="rgba(136,146,168,0.35)" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((edge, i) => {
            const src = nodePositions[edge.source_entity_id];
            const tgt = nodePositions[edge.target_entity_id];
            if (!src || !tgt) return null;
            const strokeW = Math.max(1.5, edge.weight * 4);
            const isHovered = hoveredEdge === i;
            const mx = (src.x + tgt.x) / 2;
            const my = (src.y + tgt.y) / 2;
            const labelText = edge.label && edge.label.length > 34
              ? edge.label.slice(0, 32) + '…'
              : edge.label;
            return (
              <g key={i}>
                {/* Wide invisible hit target */}
                <line
                  x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y}
                  stroke="transparent" strokeWidth={14}
                  onMouseEnter={() => setHoveredEdge(i)}
                  onMouseLeave={() => setHoveredEdge(null)}
                  style={{ cursor: 'default' }}
                />
                <line
                  x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y}
                  stroke={isHovered ? 'rgba(0,229,204,0.7)' : 'rgba(136,146,168,0.18)'}
                  strokeWidth={isHovered ? strokeW + 1 : strokeW}
                  markerEnd="url(#arrowhead)"
                  style={{ pointerEvents: 'none' }}
                />
                {isHovered && (
                  <g style={{ pointerEvents: 'none' }}>
                    <rect
                      x={mx - labelText.length * 3.1} y={my - 19}
                      width={labelText.length * 6.2 + 8} height={15}
                      fill="rgba(12,18,28,0.9)" rx="2"
                    />
                    <text
                      x={mx + 2} y={my - 8}
                      textAnchor="middle"
                      fill="rgba(0,229,204,0.9)"
                      fontSize="9"
                      fontFamily="monospace"
                    >
                      {labelText}
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = nodePositions[node.entity_id];
            if (!pos) return null;
            const color = getNodeColor(node.entity_type);
            const isSelected = selectedEntity === node.entity_id;
            const isHov = hoveredNode === node.entity_id;
            return (
              <g
                key={node.entity_id}
                onMouseEnter={() => setHoveredNode(node.entity_id)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: 'default' }}
              >
                <rect
                  x={pos.x - 22} y={pos.y - 22} width={44} height={44}
                  fill={`${color}${isHov ? '25' : '15'}`}
                  stroke={isSelected ? color : isHov ? `${color}90` : `${color}45`}
                  strokeWidth={isSelected ? 2 : isHov ? 1.5 : 1}
                  style={{ filter: isSelected ? `drop-shadow(0 0 8px ${color}60)` : isHov ? `drop-shadow(0 0 4px ${color}40)` : 'none' }}
                />
                <text x={pos.x} y={pos.y + 5} textAnchor="middle" fill={color} fontSize="13" fontWeight="bold" fontFamily="monospace">
                  {node.name.charAt(0).toUpperCase()}
                </text>
                <text x={pos.x} y={pos.y + 34} textAnchor="middle" fill="rgba(200,210,230,0.85)" fontSize="9" fontFamily="sans-serif">
                  {node.name.length > 12 ? node.name.slice(0, 10) + '…' : node.name}
                </text>
                <text x={pos.x} y={pos.y + 44} textAnchor="middle" fill="rgba(136,146,168,0.55)" fontSize="8" fontFamily="monospace">
                  {node.mention_count}×
                </text>
              </g>
            );
          })}

          {/* Node hover tooltip */}
          {hoveredNode && hoveredNodeData && nodePositions[hoveredNode] && (() => {
            const pos = nodePositions[hoveredNode];
            const color = getNodeColor(hoveredNodeData.entity_type);
            const aboutText = hoveredNodeData.about || 'No description yet.';
            const tipW = 175;
            const tipX = Math.min(SVG_W - tipW - 8, Math.max(8, pos.x - tipW / 2));
            const tipY = pos.y + 56 > SVG_H - 75 ? pos.y - 95 : pos.y + 56;
            const aboutLines = aboutText.match(/.{1,26}(\s|$)/g) || [aboutText.slice(0, 26)];
            const tipH = 38 + aboutLines.slice(0, 2).length * 12;
            return (
              <g style={{ pointerEvents: 'none' }}>
                <rect x={tipX} y={tipY} width={tipW} height={tipH} fill="rgba(10,15,25,0.96)" stroke={`${color}45`} strokeWidth="1" rx="2" />
                <text x={tipX + 10} y={tipY + 15} fill={color} fontSize="10" fontWeight="bold" fontFamily="sans-serif">
                  {hoveredNodeData.name}
                </text>
                <text x={tipX + 10} y={tipY + 26} fill="rgba(136,146,168,0.65)" fontSize="8" fontFamily="monospace">
                  {hoveredNodeData.entity_type} · {hoveredNodeData.mention_count} mentions
                </text>
                <line x1={tipX + 8} y1={tipY + 32} x2={tipX + tipW - 8} y2={tipY + 32} stroke="rgba(136,146,168,0.2)" strokeWidth="1" />
                {aboutLines.slice(0, 2).map((line, i) => (
                  <text key={i} x={tipX + 10} y={tipY + 43 + i * 12} fill="rgba(180,190,210,0.7)" fontSize="8.5" fontFamily="sans-serif" fontStyle="italic">
                    {line}
                  </text>
                ))}
              </g>
            );
          })()}

          {nodes.length === 0 && !isLoading && (
            <text x={SVG_W / 2} y={SVG_H / 2} textAnchor="middle" fill="rgba(136,146,168,0.4)" fontSize="13" fontFamily="sans-serif">
              No connected entities found. Try adjusting filters.
            </text>
          )}
        </svg>

        {/* Selected entity label */}
        {selectedEntity && (() => {
          const ent = entityList.find((e) => e.entity_id === selectedEntity);
          return ent ? (
            <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 bg-echo-surface border border-cyan-glow/30 text-xs" style={{ borderRadius: '2px' }}>
              <span className="text-echo-muted">Showing connections for</span>
              <span className="text-cyan-glow font-medium">{ent.name}</span>
              <button
                onClick={() => { setSelectedEntity(null); setEditingAbout(null); }}
                className="text-echo-muted hover:text-echo-text ml-1"
              >
                ×
              </button>
            </div>
          ) : null;
        })()}

        {/* Bottom controls */}
        <div
          className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 px-4 py-2 bg-echo-surface border border-echo-border"
          style={{ borderRadius: '2px' }}
        >
          {/* Type filter */}
          <div className="flex items-center gap-1">
            {TYPE_FILTERS.map((f) => (
              <button
                key={f.id}
                onClick={() => { setTypeFilter(f.id); setSelectedEntity(null); }}
                className={`flex items-center gap-1 px-2.5 py-1 text-[10px] uppercase tracking-wider border transition-all ${
                  typeFilter === f.id
                    ? 'border-cyan-glow/40 text-cyan-glow bg-cyan-glow/5'
                    : 'border-echo-border text-echo-muted hover:text-echo-text'
                }`}
                style={{ borderRadius: '2px' }}
              >
                {f.id !== 'all' && <span style={{ color: NODE_COLORS[f.id] }}>●</span>}
                {f.label}
              </button>
            ))}
          </div>

          {/* Min shared events */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-echo-muted uppercase tracking-wider">Min shared</span>
            {[1, 2, 3].map((n) => (
              <button
                key={n}
                onClick={() => setMinSharedEvents(n)}
                className={`w-7 h-6 text-[10px] font-mono border transition-all ${
                  minSharedEvents === n
                    ? 'border-cyan-glow/40 text-cyan-glow bg-cyan-glow/5'
                    : 'border-echo-border text-echo-muted hover:text-echo-text'
                }`}
                style={{ borderRadius: '2px' }}
              >
                {n === 3 ? '3+' : n}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
