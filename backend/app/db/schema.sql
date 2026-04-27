-- ============================================================
-- ECHOMIND FINAL MVP SCHEMA (LOCKED)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

--------------------------------------------------
-- USERS
--------------------------------------------------
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone_number TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------
-- USER SETTINGS (MERGED)
--------------------------------------------------
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,

    -- profile
    about TEXT,
    profession TEXT,
    organization TEXT,
    timezone TEXT,

    -- LLM behavior
    llm_tone TEXT DEFAULT 'professional',
    response_style TEXT DEFAULT 'concise',

    -- API tokens (store encrypted externally ideally)
    api_keys JSONB DEFAULT '{}',

    -- preferences
    salience_threshold FLOAT DEFAULT 0.6,

    metadata JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------
-- DATA SOURCES
--------------------------------------------------
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ingestion_mode TEXT CHECK (ingestion_mode IN ('scheduled','manual','push')),
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------
-- MEMORY CHUNKS (CORE)
--------------------------------------------------
CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    source_id UUID REFERENCES data_sources(id),

    external_message_id TEXT,

    timestamp TIMESTAMPTZ NOT NULL,
    participants JSONB,

    content_type TEXT CHECK (content_type IN ('text','email','document','audio','gmeet')),

    raw_content TEXT NOT NULL,
    embedding VECTOR(1536),

    -- salience
    initial_salience FLOAT DEFAULT 0,
    refined_salience FLOAT,

    -- semantic enrichment (ONLY for high salience)
    title TEXT,
    summary TEXT,
    keywords TEXT[],
    tags TEXT[],

    is_processed BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_id, external_message_id)
);

--------------------------------------------------
-- ENTITIES
--------------------------------------------------
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),

    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,

    entity_type TEXT CHECK (entity_type IN (
        'person','project','organization',
        'tool','technology','topic','task',
        'location','file','concept'
    )),

    mention_count INTEGER DEFAULT 1,
    salience_score FLOAT DEFAULT 0.5,
    last_seen TIMESTAMPTZ,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (normalized_name, entity_type, user_id)
);

--------------------------------------------------
-- EVENTS
--------------------------------------------------
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),

    title TEXT NOT NULL,
    summary TEXT,

    event_type TEXT CHECK (event_type IN (
        'decision','meeting','task',
        'discussion','milestone','other'
    )),

    start_time TIMESTAMPTZ,
    salience_score FLOAT,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------
-- ENTITY ↔ EVENT LINKS
--------------------------------------------------
CREATE TABLE entity_event_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,

    role TEXT CHECK (role IN (
        'participant','subject','organizer',
        'mentioned','owner','assignee','reporter'
    )),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (entity_id, event_id, role)
);

--------------------------------------------------
-- EVENT ↔ MEMORY LINKS
--------------------------------------------------
CREATE TABLE event_memory_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    memory_chunk_id UUID REFERENCES memory_chunks(id) ON DELETE CASCADE,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (event_id, memory_chunk_id)
);

--------------------------------------------------
-- USER QUERIES (RAG TRACKING)
--------------------------------------------------
CREATE TABLE user_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),

    query TEXT NOT NULL,
    response TEXT,

    source TEXT CHECK (source IN ('text','voice')),
    latency_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------
-- PROCESSING QUEUE
--------------------------------------------------
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_chunk_id UUID REFERENCES memory_chunks(id) ON DELETE CASCADE,

    status TEXT CHECK (status IN ('pending','processing','done','retry','failed')),
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(memory_chunk_id)
);

--------------------------------------------------
-- MEDIA FILES
--------------------------------------------------
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_chunk_id UUID REFERENCES memory_chunks(id) ON DELETE CASCADE,

    original_filename TEXT,
    media_type TEXT CHECK (media_type IN ('image','audio','document','video')),
    mime_type TEXT,

    local_path TEXT,
    size_bytes BIGINT,

    extracted_content TEXT,
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------
-- SYSTEM LOGS
--------------------------------------------------
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    level TEXT CHECK (level IN ('info','warning','error','critical')),
    component TEXT,
    message TEXT,

    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------
-- OPTIONAL: TRACKED ENTITIES (KEEP FOR DEMO BOOST)
--------------------------------------------------
CREATE TABLE tracked_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),

    normalized_name TEXT,
    entity_type TEXT,
    boost_value FLOAT DEFAULT 0.2,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, normalized_name)
);

--------------------------------------------------
-- INDEXES (IMPORTANT FOR PERFORMANCE + DEMO)
--------------------------------------------------

CREATE INDEX idx_memory_chunks_unprocessed
ON memory_chunks (is_processed, timestamp)
WHERE is_processed = FALSE;

CREATE INDEX idx_entities_normalized
ON entities (normalized_name, entity_type);

CREATE INDEX idx_entity_event_links_event
ON entity_event_links (event_id);

CREATE INDEX idx_entity_event_links_entity
ON entity_event_links (entity_id);

CREATE INDEX idx_event_memory_links_event
ON event_memory_links (event_id);

CREATE INDEX idx_processing_queue_status
ON processing_queue (status);