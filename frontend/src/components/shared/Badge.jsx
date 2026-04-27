import React from 'react';
import { SOURCE_COLORS, SOURCE_LABELS } from '../../data/mockData';

const STATUS_STYLES = {
  active: { bg: 'rgba(34, 197, 94, 0.15)', text: '#4ade80', border: 'rgba(34, 197, 94, 0.3)' },
  inactive: { bg: 'rgba(107, 114, 128, 0.15)', text: '#9ca3af', border: 'rgba(107, 114, 128, 0.3)' },
  error: { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: 'rgba(239, 68, 68, 0.3)' },
  auth_required: { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: 'rgba(245, 158, 11, 0.3)' },
};

const STATUS_LABELS = {
  active: 'Active',
  inactive: 'Inactive',
  error: 'Error',
  auth_required: 'Auth Required',
};

const COST_STYLES = {
  '$': { bg: 'rgba(34, 197, 94, 0.15)', text: '#4ade80' },
  '$$': { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24' },
  '$$$': { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171' },
};

export function SourceBadge({ source }) {
  const color = SOURCE_COLORS[source] || '#8892a8';
  const label = SOURCE_LABELS[source] || source;

  return (
    <span
      className="tag-chip"
      style={{
        background: `${color}18`,
        color: color,
        border: `1px solid ${color}30`,
      }}
    >
      {label}
    </span>
  );
}

export function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.inactive;
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      className="tag-chip"
      style={{
        background: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
      }}
    >
      {label}
    </span>
  );
}

export function CostBadge({ tier }) {
  const style = COST_STYLES[tier] || COST_STYLES['$'];

  return (
    <span
      className="tag-chip"
      style={{
        background: style.bg,
        color: style.text,
      }}
    >
      {tier}
    </span>
  );
}

export function ModelBadge({ model }) {
  return (
    <span className="tag-chip" style={{ background: 'rgba(0, 229, 204, 0.12)', color: '#00e5cc', border: '1px solid rgba(0, 229, 204, 0.25)' }}>
      {model}
    </span>
  );
}

export function PriorityBadge({ priority }) {
  const styles = {
    high: { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', label: 'HIGH' },
    medium: { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', label: 'MED' },
    low: { bg: 'rgba(107, 114, 128, 0.15)', text: '#9ca3af', label: 'LOW' },
  };
  const s = styles[priority] || styles.low;

  return (
    <span className="tag-chip" style={{ background: s.bg, color: s.text }}>
      {s.label}
    </span>
  );
}

export function TypeBadge({ type }) {
  const styles = {
    person: { bg: 'rgba(0, 229, 204, 0.12)', text: '#00e5cc' },
    organization: { bg: 'rgba(245, 158, 11, 0.12)', text: '#fbbf24' },
    place: { bg: 'rgba(192, 132, 252, 0.12)', text: '#c084fc' },
  };
  const s = styles[type] || styles.person;

  return (
    <span className="tag-chip" style={{ background: s.bg, color: s.text }}>
      {type}
    </span>
  );
}
