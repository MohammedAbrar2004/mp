const BASE = 'http://localhost:8000';

async function request(method, path, body, isFormData = false) {
  const opts = { method };
  if (body) {
    if (isFormData) {
      opts.body = body;
    } else {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Health ────────────────────────────────────────────────────────────────────
export const healthCheck = () => request('GET', '/health');

// ── Query ─────────────────────────────────────────────────────────────────────
export const postQuery = (query) => request('POST', '/query', { query });

export const postVoiceQuery = (audioBlob) => {
  const fd = new FormData();
  fd.append('file', audioBlob, 'query.webm');
  return request('POST', '/query/voice', fd, true);
};

export const getQueryHistory = (limit = 20, offset = 0) =>
  request('GET', `/query/history?limit=${limit}&offset=${offset}`);

export const getSyncStatus = () => request('GET', '/query/sync-status');

// ── Memory ────────────────────────────────────────────────────────────────────
export const getMemoryChunks = ({
  search = '',
  connector_source = '',
  salience_min = 0,
  salience_max = 1,
  sort = 'newest',
  page = 1,
  per_page = 6,
} = {}) => {
  const params = new URLSearchParams({
    search,
    connector_source,
    salience_min,
    salience_max,
    sort,
    page,
    per_page,
  });
  return request('GET', `/memory/chunks?${params}`);
};

export const getChunkDetail = (chunkId) =>
  request('GET', `/memory/chunks/${chunkId}`);

// ── Ingest ────────────────────────────────────────────────────────────────────
export const ingestText = ({ content, title = '', source_label = 'manual', tags = '', people = '' }) => {
  const fd = new FormData();
  fd.append('content', content);
  fd.append('title', title);
  fd.append('source_label', source_label);
  fd.append('tags', tags);
  fd.append('people', people);
  return request('POST', '/ingest/text', fd, true);
};

export const ingestVoice = ({ file, title = '', tags = '' }) => {
  const fd = new FormData();
  fd.append('file', file, file.name || 'voice_note.webm');
  fd.append('title', title);
  fd.append('tags', tags);
  return request('POST', '/ingest/voice', fd, true);
};

export const ingestDocument = ({ file, title = '', author = '', tags = '', description = '' }) => {
  const fd = new FormData();
  fd.append('file', file, file.name);
  fd.append('title', title);
  fd.append('author', author);
  fd.append('tags', tags);
  fd.append('description', description);
  return request('POST', '/ingest/document', fd, true);
};

// ── Relations ─────────────────────────────────────────────────────────────────
export const getRelationEntities = () => request('GET', '/relations/entities');

export const getRelationGraph = ({ entity_id = '', min_shared_events = 1, type_filter = 'all' } = {}) => {
  const params = new URLSearchParams({ entity_id, min_shared_events, type_filter });
  return request('GET', `/relations/graph?${params}`);
};

export const updateEntityAbout = (entityId, about) =>
  request('PUT', `/relations/entities/${entityId}/about`, { about });

// ── Connectors ────────────────────────────────────────────────────────────────
export const getConnectorStatus = () => request('GET', '/connectors/status');

export const getIngestionRuns = (connector = '', limit = 20) => {
  const params = new URLSearchParams({ connector, limit });
  return request('GET', `/connectors/runs?${params}`);
};

export const getConnectorLogs = (connector, limit = 50) =>
  request('GET', `/connectors/logs?connector=${connector}&limit=${limit}`);

export const syncConnector = (connector) =>
  request('POST', `/connectors/${connector}/sync`);

export const pauseConnector = (connector, is_active) =>
  request('PATCH', `/connectors/${connector}/pause`, { is_active });

export const reauthWhatsapp = () => request('POST', '/connectors/whatsapp/reauth');

export const deleteGmailToken = () => request('DELETE', '/connectors/gmail/token');

export const deleteCalendarToken = () => request('DELETE', '/connectors/calendar/token');

// ── Settings ──────────────────────────────────────────────────────────────────
export const getProfile = () => request('GET', '/settings/profile');
export const updateProfile = (data) => request('PUT', '/settings/profile', data);

export const getAIModel = () => request('GET', '/settings/ai-model');
export const updateAIModel = (data) => request('PUT', '/settings/ai-model', data);

export const getTrackedEntities = () => request('GET', '/settings/tracked-entities');
export const searchEntities = (q) => request('GET', `/settings/entities/search?q=${encodeURIComponent(q)}`);
export const addTrackedEntity = (data) => request('POST', '/settings/tracked-entities', data);
export const updateTrackedEntity = (id, boost_value) =>
  request('PUT', `/settings/tracked-entities/${id}`, { boost_value });
export const deleteTrackedEntity = (id) =>
  request('DELETE', `/settings/tracked-entities/${id}`);
