import React, { useState } from 'react';
import { Plus, Trash2, Save, RotateCcw } from 'lucide-react';
import { salienceConfig, SOURCE_LABELS } from '../../data/mockData';



export default function SalienceView() {
  const [config, setConfig] = useState(salienceConfig);
  const [newKeyword, setNewKeyword] = useState('');
  const [newWeight, setNewWeight] = useState(1.5);
  const [editingRule, setEditingRule] = useState(null);

  const addKeywordRule = () => {
    if (!newKeyword.trim()) return;
    const rule = {
      id: `kr-${Date.now()}`,
      keyword: newKeyword.trim().toLowerCase(),
      weight: newWeight,
    };
    setConfig((prev) => ({
      ...prev,
      keywordRules: [...prev.keywordRules, rule],
    }));
    setNewKeyword('');
    setNewWeight(1.5);
  };

  const deleteRule = (id) => {
    setConfig((prev) => ({
      ...prev,
      keywordRules: prev.keywordRules.filter((r) => r.id !== id),
    }));
  };

  const updateEntityWeight = (type, value) => {
    setConfig((prev) => ({
      ...prev,
      entityTypeWeights: { ...prev.entityTypeWeights, [type]: value },
    }));
  };

  const updateSourceWeight = (source, value) => {
    setConfig((prev) => ({
      ...prev,
      sourceWeights: { ...prev.sourceWeights, [source]: value },
    }));
  };

  const handleReset = () => {
    setConfig(salienceConfig);
  };



  return (
    <div className="h-full flex overflow-hidden">
      {/* Left column */}
      <div className="flex-1 border-r border-echo-border overflow-y-auto p-5 space-y-6">
        {/* Keyword Rules */}
        <div>
          <h3 className="text-xs font-semibold text-echo-bright uppercase tracking-wider mb-3">Keyword Rules</h3>

          {/* Add new */}
          <div className="flex items-center gap-2 mb-3">
            <input
              type="text"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              placeholder="Add keyword..."
              className="flex-1 px-3 py-1.5 bg-echo-bg border border-echo-border text-xs text-echo-text placeholder:text-echo-muted/40 focus:outline-none glow-input"
              style={{ borderRadius: '2px' }}
              onKeyDown={(e) => e.key === 'Enter' && addKeywordRule()}
            />
            <input
              type="number"
              value={newWeight}
              onChange={(e) => setNewWeight(parseFloat(e.target.value))}
              min="0.1" max="5" step="0.1"
              className="w-16 px-2 py-1.5 bg-echo-bg border border-echo-border text-xs font-mono text-echo-text focus:outline-none glow-input"
              style={{ borderRadius: '2px' }}
            />
            <button
              onClick={addKeywordRule}
              className="p-1.5 text-cyan-glow hover:bg-cyan-glow/10 transition-colors"
              style={{ borderRadius: '2px' }}
            >
              <Plus size={14} />
            </button>
          </div>

          {/* Rules table */}
          <div className="border border-echo-border" style={{ borderRadius: '2px' }}>
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-echo-panel">
                  <th className="text-left px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Keyword</th>
                  <th className="text-left px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Weight</th>
                  <th className="text-right px-3 py-2 text-[10px] text-echo-muted uppercase tracking-wider font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {config.keywordRules.map((rule) => (
                  <tr key={rule.id} className="border-t border-echo-border hover:bg-echo-hover transition-colors">
                    <td className="px-3 py-2 font-mono text-echo-text">{rule.keyword}</td>
                    <td className="px-3 py-2 font-mono text-cyan-glow">{rule.weight}×</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => deleteRule(rule.id)}
                        className="p-1 text-echo-muted hover:text-red-400 transition-colors"
                      >
                        <Trash2 size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Save / Reset */}
        <div className="flex items-center gap-3">
          <button
            className="flex items-center gap-2 px-5 py-2.5 bg-cyan-glow/15 text-cyan-glow border border-cyan-glow/30 hover:bg-cyan-glow/25 transition-all text-xs font-medium"
            style={{ borderRadius: '2px' }}
          >
            <Save size={14} />
            Save Configuration
          </button>
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2.5 text-echo-muted border border-echo-border hover:bg-echo-hover transition-colors text-xs"
            style={{ borderRadius: '2px' }}
          >
            <RotateCcw size={14} />
            Reset to Defaults
          </button>
        </div>

        {/* Entity Type Weights */}
        <div>
          <h3 className="text-xs font-semibold text-echo-bright uppercase tracking-wider mb-3">Entity Type Weights</h3>
          <div className="space-y-3">
            {Object.entries(config.entityTypeWeights).map(([type, weight]) => (
              <div key={type} className="flex items-center gap-3">
                <span className="text-xs text-echo-muted capitalize w-24">{type}</span>
                <input
                  type="range"
                  min="0" max="3" step="0.1"
                  value={weight}
                  onChange={(e) => updateEntityWeight(type, parseFloat(e.target.value))}
                  className="flex-1 accent-cyan-500"
                />
                <span className="text-xs font-mono text-cyan-glow w-8">{weight.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Source Weights */}
        <div>
          <h3 className="text-xs font-semibold text-echo-bright uppercase tracking-wider mb-3">Source Weights</h3>
          <div className="space-y-3">
            {Object.entries(config.sourceWeights).map(([source, weight]) => (
              <div key={source} className="flex items-center gap-3">
                <span className="text-xs text-echo-muted w-24">{SOURCE_LABELS[source] || source}</span>
                <input
                  type="range"
                  min="0" max="3" step="0.1"
                  value={weight}
                  onChange={(e) => updateSourceWeight(source, parseFloat(e.target.value))}
                  className="flex-1 accent-cyan-500"
                />
                <span className="text-xs font-mono text-cyan-glow w-8">{weight.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>


    </div>
  );
}
