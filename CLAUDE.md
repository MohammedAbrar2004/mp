# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EchoMind** is an AI-powered cognitive memory system that ingests, structures, and retrieves information from WhatsApp, Gmail, Google Calendar, and manual uploads. It is a single-user prototype currently in **Phase 3** (Preprocessing Layer), with Phases 1–2 (Connectors + Ingestion Pipeline) complete.

## Commands

### Backend (Python / FastAPI)
```bash
# Activate environment
conda activate mp

# Initialize or re-run schema migrations
cd backend && python app/db/init_db.py

# Run the FastAPI server
cd backend && uvicorn app.api.whatsapp_receiver:app --host 127.0.0.1 --port 8000 --reload

# Run the ingestion pipeline manually
cd backend 
python -m pipelines.ingestion_pipeline
```

### WhatsApp Client (Node.js / Baileys)
```bash
cd api/whatsapp && npm install
cd api/whatsapp && npm start
```

### Tests
```bash
# Connector unit tests (run from repo root)
python backend/tests/test_whatsapp.py
python backend/tests/test_gmail.py
python backend/tests/test_calendar.py

# Pipeline integration test
cd backend && python pipelines/test_pipeline.py

# Individual connector smoke tests
cd backend && python -m app.connectors.whatsapp.test_connector
cd backend && python -m app.connectors.gmail.test_client
cd backend && python -m app.connectors.calendar.test_client
```

There is no `pytest.ini` or Makefile; tests are standalone Python scripts.

## Architecture

### Layered Design
```
Layer 1 — Connectors (complete):   WhatsApp · Gmail · Calendar · Manual
Layer 2 — Ingestion Pipeline (complete): MediaService → DB writes → dedup
Layer 3 — Preprocessing (in progress): Cleaning → Salience → Embeddings
Layer 4 — Retrieval Engine (planned)
Layer 5 — AI Assistant (planned)
```

### Data Flow
```
External Source
  → Connector (pure — returns NormalizedInput + PendingMedia, no side effects)
  → ingestion_pipeline.py
      → MediaService  →  saves files to backend/media/{documents,audio}/
      → Repository    →  inserts into memory_chunks + media_files
      → Deduplication via UNIQUE(source_id, external_message_id) ON CONFLICT DO NOTHING
```

### Key Contracts
- **`backend/models/normalized_input.py`** — `NormalizedInput` and `PendingMedia` are the universal data contracts. Every connector must return these; no connector may write to the DB or disk.
- **`backend/app/db/schema.sql`** — PostgreSQL schema with pgvector. Core tables: `memory_chunks`, `media_files`, `data_sources`, `users`, `processing_queue`.

### Important Invariants
- **Connectors are pure.** They parse and return; never write DB, disk, or business logic.
- **Raw content is immutable.** `memory_chunks.raw_content` is never modified after insert. Cleaned content goes into `memory_chunks.content` (added by preprocessing).
- **Media lives separately.** `memory_chunks.content` does not embed media; media text lives in `media_files.cleaned_content`.
- **Single hardcoded user.** UUID `5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9` is used throughout the pipeline (see `pipelines/ingestion_pipeline.py`).
- **Source IDs are currently hardcoded** in the pipeline (TODO: fetch from `data_sources` table).

### Two-Component Runtime
The system requires **two processes running simultaneously**:
1. `uvicorn` (Python) — receives webhooks from the Node client
2. `npm start` in `api/whatsapp/` — Baileys WhatsApp client that pushes messages to the FastAPI endpoint

## Environment Variables

Stored in `backend/.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mp
DB_USER=postgres
DB_PASSWORD=<password>
MEDIA_BASE_DIR=./media
RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000
```

OAuth credential files (Gmail, Calendar) are stored in `backend/app/connectors/gmail/` and `backend/app/connectors/calendar/` — never commit these.

## Current Development Focus

Phase 3 — Preprocessing Layer. Design doc: `backend/preprocessing/preprocessing.md`. The planned services are: Media Processing → Text Cleaning → Salience Scoring → Embedding Generation. These will populate `memory_chunks.content`, `memory_chunks.initial_salience`, and `memory_chunks.embedding`.

See `frontend/todo.md` for high-priority known issues (metadata standardization, multi-calendar handling, etc.).
