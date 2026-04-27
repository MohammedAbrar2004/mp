import React from 'react';
import { getSalienceColor } from '../../data/mockData';

export default function SalienceBar({ score, width = '100%', showLabel = false }) {
  const color = getSalienceColor(score);
  const pct = Math.round(score * 100);

  return (
    <div className="flex items-center gap-2">
      <div className="salience-bar flex-1" style={{ width }}>
        <div
          className="fill"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}88, ${color})`,
          }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono" style={{ color, minWidth: 32 }}>
          {score.toFixed(2)}
        </span>
      )}
    </div>
  );
}
