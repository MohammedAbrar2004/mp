import React, { useState } from 'react';
import { CheckCircle2, Clock, Handshake, MoreHorizontal, Check, AlarmClock, CalendarDays } from 'lucide-react';
import { commitments, formatDate } from '../../data/mockData';
import SourceIcon from '../shared/SourceIcon';
import { PriorityBadge, SourceBadge } from '../shared/Badge';

const COLUMNS = [
  { id: 'openTasks', title: 'Open Tasks', icon: CheckCircle2, color: '#00e5cc' },
  { id: 'upcomingEvents', title: 'Upcoming Events', icon: CalendarDays, color: '#fbbf24' },
  { id: 'promises', title: 'Promises / Follow-ups', icon: Handshake, color: '#c084fc' },
];

export default function CommitmentsView() {
  const [items, setItems] = useState(commitments);

  const markComplete = (column, itemId) => {
    setItems((prev) => ({
      ...prev,
      [column]: prev[column].map((item) =>
        item.id === itemId ? { ...item, status: item.status === 'done' ? 'open' : 'done' } : item
      ),
    }));
  };

  const snoozeItem = (column, itemId) => {
    // TODO: API call to snooze
    setItems((prev) => ({
      ...prev,
      [column]: prev[column].map((item) =>
        item.id === itemId
          ? {
            ...item,
            dueDate: item.dueDate
              ? new Date(new Date(item.dueDate).getTime() + 3 * 86400000).toISOString().split('T')[0]
              : null,
          }
          : item
      ),
    }));
  };

  const getPriorityBorderColor = (priority) => {
    switch (priority) {
      case 'high': return '#f87171';
      case 'medium': return '#fbbf24';
      default: return '#4b5563';
    }
  };

  return (
    <div className="h-full flex gap-4 p-4 overflow-hidden">
      {COLUMNS.map(({ id, title, icon: Icon, color }) => (
        <div key={id} className="flex-1 flex flex-col min-w-0">
          {/* Column header */}
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-echo-border">
            <Icon size={16} style={{ color }} />
            <span className="text-xs font-semibold text-echo-bright uppercase tracking-wider">{title}</span>
            <span className="ml-auto text-[10px] font-mono text-echo-muted bg-echo-bg px-1.5 py-0.5" style={{ borderRadius: '2px' }}>
              {items[id]?.length || 0}
            </span>
          </div>

          {/* Cards */}
          <div className="flex-1 overflow-y-auto space-y-2 kanban-col">
            {items[id]?.map((item) => (
              <div
                key={item.id}
                className={`glass-card p-3 hover-lift transition-all duration-200 ${item.status === 'done' ? 'opacity-50' : ''
                  }`}
                style={{
                  borderRadius: '2px',
                  borderLeft: `3px solid ${getPriorityBorderColor(item.priority)}`,
                }}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <p className={`text-xs font-medium leading-relaxed ${item.status === 'done' ? 'line-through text-echo-muted' : 'text-echo-text'
                    }`}>
                    {item.title}
                  </p>
                  <PriorityBadge priority={item.priority} />
                </div>

                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <SourceIcon source={item.source} size={11} />
                  <SourceBadge source={item.source} />
                  {item.dueDate && (
                    <span className="text-[10px] font-mono text-echo-muted flex items-center gap-1">
                      <Clock size={9} />
                      {formatDate(item.dueDate)}
                    </span>
                  )}
                </div>

                {item.entities.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {item.entities.map((ent) => (
                      <span key={ent} className="text-[10px] font-mono text-cyan-glow bg-cyan-glow/8 px-1.5 py-0.5" style={{ borderRadius: '2px' }}>
                        {ent}
                      </span>
                    ))}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-1 pt-2 border-t border-echo-border">
                  <button
                    onClick={() => markComplete(id, item.id)}
                    className={`flex items-center gap-1 px-2 py-1 text-[10px] transition-colors ${item.status === 'done'
                        ? 'text-green-400 bg-green-400/10'
                        : 'text-echo-muted hover:text-green-400 hover:bg-green-400/10'
                      }`}
                    style={{ borderRadius: '2px' }}
                  >
                    <Check size={10} />
                    {item.status === 'done' ? 'Done' : 'Complete'}
                  </button>
                  <button
                    onClick={() => snoozeItem(id, item.id)}
                    className="flex items-center gap-1 px-2 py-1 text-[10px] text-echo-muted hover:text-amber-400 hover:bg-amber-400/10 transition-colors"
                    style={{ borderRadius: '2px' }}
                  >
                    <AlarmClock size={10} />
                    Snooze
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
