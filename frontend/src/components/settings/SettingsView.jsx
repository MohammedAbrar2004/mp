import React, { useState, useEffect, useRef } from 'react';
import { User, Bot, Users, Eye, EyeOff, Plus, Trash2, Search, Loader2, Check } from 'lucide-react';
import {
  getProfile, updateProfile, getAIModel, updateAIModel,
  getTrackedEntities, searchEntities, addTrackedEntity, deleteTrackedEntity, updateTrackedEntity,
} from '../../api/client';
import { TypeBadge, CostBadge } from '../shared/Badge';

const TABS = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'aiModel', label: 'AI Model', icon: Bot },
  { id: 'trackedEntities', label: 'Tracked Entities', icon: Users },
];

const AI_MODELS = [
  { id: 'ollama', name: 'Ollama', cost: 'Free' },
  { id: 'gemini', name: 'Gemini', cost: '$$' },
  { id: 'groq', name: 'Groq', cost: '$' },
];

export default function SettingsView() {
  const [activeTab, setActiveTab] = useState('profile');

  // Profile state
  const [profile, setProfile] = useState({ name: '', email: '', phone: '', about: '', profession: '' });
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);

  // AI model state
  const [aiSettings, setAiSettings] = useState({ llm_tone: 'groq', response_style: 'balanced', api_keys: {}, answer_persona: '' });
  const [showApiKeys, setShowApiKeys] = useState({});
  const [aiSaved, setAiSaved] = useState(false);
  const [aiSaving, setAiSaving] = useState(false);

  // Tracked entities state
  const [trackedList, setTrackedList] = useState([]);
  const [entitySearch, setEntitySearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [newEntityType, setNewEntityType] = useState('person');
  const searchDebounce = useRef(null);

  useEffect(() => {
    getProfile().then(setProfile).catch(() => {});
    getAIModel().then(setAiSettings).catch(() => {});
    getTrackedEntities().then((d) => setTrackedList(d.tracked || [])).catch(() => {});
  }, []);

  const handleEntitySearch = (val) => {
    setEntitySearch(val);
    clearTimeout(searchDebounce.current);
    if (!val.trim()) { setSearchResults([]); return; }
    searchDebounce.current = setTimeout(() => {
      searchEntities(val).then((d) => setSearchResults(d.entities || [])).catch(() => {});
    }, 250);
  };

  const handleAddEntity = async (entity) => {
    try {
      const res = await addTrackedEntity({ normalized_name: entity.name.toLowerCase(), entity_type: entity.entity_type || newEntityType, boost_value: 0.2 });
      await getTrackedEntities().then((d) => setTrackedList(d.tracked || []));
      setEntitySearch('');
      setSearchResults([]);
    } catch { }
  };

  const handleDeleteTracked = async (id) => {
    try {
      await deleteTrackedEntity(id);
      setTrackedList((prev) => prev.filter((t) => t.tracked_entity_id !== id));
    } catch { }
  };

  const handleToggleBoost = async (entity) => {
    const newBoost = entity.boost_value > 0 ? 0 : 0.2;
    try {
      await updateTrackedEntity(entity.tracked_entity_id, newBoost);
      setTrackedList((prev) => prev.map((t) => t.tracked_entity_id === entity.tracked_entity_id ? { ...t, boost_value: newBoost } : t));
    } catch { }
  };

  const saveProfile = async () => {
    setProfileSaving(true);
    try {
      await updateProfile(profile);
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2000);
    } catch { }
    finally { setProfileSaving(false); }
  };

  const saveAIModel = async () => {
    setAiSaving(true);
    try {
      await updateAIModel(aiSettings);
      setAiSaved(true);
      setTimeout(() => setAiSaved(false), 2000);
    } catch { }
    finally { setAiSaving(false); }
  };

  const InputField = ({ label, value, onChange, placeholder, multiline = false, type = 'text' }) => (
    <div>
      <label className="text-[10px] text-echo-muted uppercase tracking-wider block mb-1.5">{label}</label>
      {multiline ? (
        <textarea value={value || ''} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={3}
          className="w-full px-3 py-2 bg-echo-bg border border-echo-border text-sm text-echo-text placeholder:text-echo-muted/40 focus:outline-none glow-input resize-none"
          style={{ borderRadius: '2px' }} />
      ) : (
        <input type={type} value={value || ''} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
          className="w-full px-3 py-2 bg-echo-bg border border-echo-border text-sm text-echo-text placeholder:text-echo-muted/40 focus:outline-none glow-input"
          style={{ borderRadius: '2px' }} />
      )}
    </div>
  );

  const Toggle = ({ checked, onChange }) => (
    <div onClick={onChange} className={`w-9 h-5 flex items-center px-0.5 transition-colors cursor-pointer ${checked ? 'bg-cyan-glow/30' : 'bg-echo-border'}`} style={{ borderRadius: '2px' }}>
      <div className={`w-4 h-4 transition-transform ${checked ? 'translate-x-4 bg-cyan-glow' : 'translate-x-0 bg-echo-muted'}`} style={{ borderRadius: '1px' }} />
    </div>
  );

  return (
    <div className="h-full flex overflow-hidden">
      <div className="w-[200px] flex-shrink-0 border-r border-echo-border p-2">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-all duration-150 mb-0.5 ${activeTab === id ? 'bg-cyan-glow/8 text-cyan-glow' : 'text-echo-muted hover:text-echo-text hover:bg-echo-hover'}`}
            style={{ borderRadius: '2px' }}>
            <Icon size={14} />
            <span className="text-xs">{label}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl space-y-5">

          {/* PROFILE TAB */}
          {activeTab === 'profile' && (
            <>
              <h2 className="text-sm font-semibold text-echo-bright mb-4">Profile</h2>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-echo-bg border border-echo-border flex items-center justify-center" style={{ borderRadius: '2px' }}>
                  <span className="text-xl font-mono text-echo-muted">{(profile.name || 'U').charAt(0)}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <InputField label="Name" value={profile.name} onChange={(v) => setProfile((p) => ({ ...p, name: v }))} />
                <InputField label="Role / Occupation" value={profile.profession} onChange={(v) => setProfile((p) => ({ ...p, profession: v }))} placeholder="e.g. Founder & Product Engineer" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <InputField label="Phone Number" value={profile.phone} onChange={(v) => setProfile((p) => ({ ...p, phone: v }))} placeholder="+91 98765 43210" />
                <InputField label="Email" value={profile.email} onChange={(v) => setProfile((p) => ({ ...p, email: v }))} placeholder="you@example.com" type="email" />
              </div>
              <InputField label="About Me (used as context for AI)" value={profile.about} onChange={(v) => setProfile((p) => ({ ...p, about: v }))} multiline placeholder="Tell the AI about yourself..." />

              <button onClick={saveProfile} disabled={profileSaving}
                className="flex items-center gap-2 px-4 py-2 text-xs bg-cyan-glow/15 text-cyan-glow border border-cyan-glow/30 hover:bg-cyan-glow/25 transition-all disabled:opacity-50"
                style={{ borderRadius: '2px' }}>
                {profileSaving ? <Loader2 size={12} className="animate-spin" /> : profileSaved ? <Check size={12} /> : null}
                {profileSaved ? 'Saved!' : 'Save Profile'}
              </button>
            </>
          )}

          {/* AI MODEL TAB */}
          {activeTab === 'aiModel' && (
            <>
              <h2 className="text-sm font-semibold text-echo-bright mb-4">AI Model Configuration</h2>

              <div>
                <label className="text-[10px] text-echo-muted uppercase tracking-wider block mb-2">Model</label>
                <div className="space-y-1.5">
                  {AI_MODELS.map((model) => (
                    <button key={model.id} onClick={() => setAiSettings((s) => ({ ...s, llm_tone: model.id }))}
                      className={`w-full flex items-center justify-between px-4 py-3 border transition-all ${aiSettings.llm_tone === model.id ? 'border-cyan-glow/40 bg-cyan-glow/5' : 'border-echo-border hover:bg-echo-hover'}`}
                      style={{ borderRadius: '2px' }}>
                      <span className={`text-sm ${aiSettings.llm_tone === model.id ? 'text-echo-bright' : 'text-echo-text'}`}>{model.name}</span>
                      <CostBadge tier={model.cost} />
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-5">
                <span className="text-[10px] text-echo-muted uppercase tracking-wider block mb-2">API Keys</span>
                {['gemini', 'groq'].map((provider) => (
                  <div key={provider} className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-echo-muted w-16 capitalize">{provider}</span>
                    <div className="relative flex-1">
                      <input
                        type={showApiKeys[provider] ? 'text' : 'password'}
                        value={(aiSettings.api_keys || {})[provider] || ''}
                        onChange={(e) => setAiSettings((s) => ({ ...s, api_keys: { ...s.api_keys, [provider]: e.target.value } }))}
                        placeholder={`${provider} API key`}
                        className="w-full px-3 py-1.5 pr-10 bg-echo-bg border border-echo-border text-xs font-mono text-echo-text focus:outline-none glow-input"
                        style={{ borderRadius: '2px' }} />
                      <button onClick={() => setShowApiKeys((p) => ({ ...p, [provider]: !p[provider] }))}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-echo-muted hover:text-echo-text transition-colors">
                        {showApiKeys[provider] ? <EyeOff size={12} /> : <Eye size={12} />}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-5">
                <label className="text-[10px] text-echo-muted uppercase tracking-wider block mb-2">Response Style</label>
                <div className="flex gap-2">
                  {['concise', 'balanced', 'detailed'].map((style) => (
                    <button key={style} onClick={() => setAiSettings((s) => ({ ...s, response_style: style }))}
                      className={`px-4 py-2 text-xs capitalize border transition-all ${aiSettings.response_style === style ? 'border-cyan-glow/40 text-cyan-glow bg-cyan-glow/5' : 'border-echo-border text-echo-muted hover:text-echo-text'}`}
                      style={{ borderRadius: '2px' }}>
                      {style}
                    </button>
                  ))}
                </div>
              </div>

              <InputField label="Answer Persona" value={aiSettings.answer_persona}
                onChange={(v) => setAiSettings((s) => ({ ...s, answer_persona: v }))}
                placeholder="Answer as a knowledgeable assistant who understands my work context..." multiline />

              <button onClick={saveAIModel} disabled={aiSaving}
                className="flex items-center gap-2 px-4 py-2 text-xs bg-cyan-glow/15 text-cyan-glow border border-cyan-glow/30 hover:bg-cyan-glow/25 transition-all disabled:opacity-50"
                style={{ borderRadius: '2px' }}>
                {aiSaving ? <Loader2 size={12} className="animate-spin" /> : aiSaved ? <Check size={12} /> : null}
                {aiSaved ? 'Saved!' : 'Save Configuration'}
              </button>
            </>
          )}

          {/* TRACKED ENTITIES TAB */}
          {activeTab === 'trackedEntities' && (
            <>
              <h2 className="text-sm font-semibold text-echo-bright mb-4">Tracked Entities</h2>

              <div className="relative mb-2">
                <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-echo-muted" />
                <input type="text" value={entitySearch} onChange={(e) => handleEntitySearch(e.target.value)}
                  placeholder="Search all entities to track..."
                  className="w-full pl-8 pr-3 py-1.5 bg-echo-bg border border-echo-border text-xs text-echo-text focus:outline-none glow-input"
                  style={{ borderRadius: '2px' }} />
              </div>

              {searchResults.length > 0 && (
                <div className="border border-echo-border bg-echo-bg mb-4 max-h-48 overflow-y-auto" style={{ borderRadius: '2px' }}>
                  {searchResults.map((e) => (
                    <button key={e.entity_id} onClick={() => handleAddEntity(e)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-echo-hover transition-colors text-left">
                      <span className="flex-1 text-echo-text">{e.name}</span>
                      <TypeBadge type={e.entity_type} />
                      <span className="text-echo-muted font-mono">{e.mention_count} mentions</span>
                      <Plus size={12} className="text-cyan-glow" />
                    </button>
                  ))}
                </div>
              )}

              <div className="space-y-1">
                {trackedList.length === 0 && (
                  <p className="text-xs text-echo-muted/50 text-center py-4">No tracked entities yet. Search above to add.</p>
                )}
                {trackedList.map((entity) => (
                  <div key={entity.tracked_entity_id} className="flex items-center gap-3 p-3 bg-echo-bg border border-echo-border hover:border-echo-muted/30 transition-colors" style={{ borderRadius: '2px' }}>
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-sm text-echo-text">{entity.normalized_name}</span>
                      <TypeBadge type={entity.entity_type} />
                    </div>
                    <Toggle checked={entity.boost_value > 0} onChange={() => handleToggleBoost(entity)} />
                    <button onClick={() => handleDeleteTracked(entity.tracked_entity_id)} className="p-1 text-echo-muted hover:text-red-400 transition-colors">
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
