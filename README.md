# EchoMind (mp) — AI-Powered Cognitive Memory System

## 🧠 Overview

EchoMind is a **single-user cognitive memory system** designed to passively capture, structure, and recall information from all major communication channels — WhatsApp, Gmail, Calendar, Google Meet, and manual inputs.

The goal is simple but powerful:

> You should never lose track of what was said, what was promised, what was scheduled, or what needs to be done.

---

## ❗ Why This Project Exists

Modern workflows are fragmented:

* Conversations happen across WhatsApp, email, meetings
* Tasks and commitments get lost in noise
* Important context is scattered and unretrievable

Humans are not built to:

* remember everything
* track conversations across platforms
* reconstruct past context accurately

---

## 🎯 What EchoMind Solves

EchoMind acts as a **personal second brain**:

* Automatically ingests data from multiple sources
* Normalizes everything into a unified structure
* Stores it in a queryable database
* Enables future retrieval like:

  * *“What did I discuss with Amaan last week?”*
  * *“What tasks are pending from my project group?”*

---

## 🏗️ System Vision (Final State)

At full maturity, EchoMind will:

### Layer 1 — Data Ingestion

* WhatsApp (real-time)(ingest pdfs, word and voice notes)
* Gmail (emails + attachments)
* Calendar (events)
* GMeet (recordings/transcripts retrieved and processed from Google Drive)
* Manual uploads

### Layer 2 — Preprocessing & Storage

* Normalize all data into a standard format
* Store raw content in database
* Store media separately
* All this with proper routing and where the data is stored which is also reflected in the corresponding DB tables

### Layer 3 — Semantic Understanding (Future)

* Extract entities (people, tasks, events)
* Build knowledge graph
* Processing of Media (PDFs, word and voice notes) and extracting entities off it and pushing that data into corresponding tables.

### Layer 4 — Retrieval Engine (Future)

* Query past context intelligently
* Combine semantic + temporal search

### Layer 5 — AI Assistant (Future)

* Answer questions
* Suggest actions
* Draft responses

---

📁 Project Structure (Initial Setup)
mp/
├── backend/
│   └── .env
│
├── api/
│   ├── whatsapp/
│   │   ├── index.js
│   │   ├── sender.js
│   │   └── config.js
│   │
│   └── (future services)
│       ├── gmail/
│       ├── gmeet/
│
└── frontend/

🧱 Planned Backend Structure (Future Expansion)
backend/
├── app/
│   ├── connectors/          # Pure connectors (no DB, no file writes)
│   │   ├── whatsapp/
│   │   ├── gmail/
│   │   ├── calendar/
│   │   ├── gmeet/
│   │   └── manual/
│   │
│   ├── db/                  # DB connection, schema, repository layer
│   │   ├── connection.py
│   │   ├── init_db.py
│   │   ├── repository.py
│   │   └── schema.sql
│   │
│   ├── services/            # Shared services (media handling, etc.)
│   │   └── media_service.py
│   │
│   ├── preprocessing/       # Cleaning + normalization logic
│   │   └── preprocessor.py
│   │
│   └── api/                 # FastAPI receiver (Python side)
│       └── receiver.py
│
├── models/                  # Data contracts
│   └── normalized_input.py
│
├── pipelines/               # Core ingestion pipeline (shared)
│   └── ingestion_pipeline.py
│
├── media/                   # Raw media storage
│   ├── audio/
│   └── documents/
│
├── tests/                   # Unit + integration tests
├── requirements.txt         # Generated via pipreqs
└── README.md

---

## 🗄️ Database

* Database Name: **mp**
* PostgreSQL will be used
* Schema will include:

  * `memory_chunks` → raw ingested data
  * `media_files` → media metadata
  * other supporting tables (later)

---

## ⚙️ Environment Setup

Inside `backend/.env`:

```env id="env1"
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mp
DB_USER=postgres
DB_PASSWORD=your_password

MEDIA_BASE_DIR=./media
RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000
```

---



## 💬 Final Goal

A system where:

```text
All your conversations → structured memory → instantly queryable
```

---

---

🧠 Architecture Note
api/ → external services (Node.js, push-based systems like WhatsApp)
backend/ → core system (connectors, pipeline, DB, services)
frontend/ → UI layer (future)


🔁 Data Flow Overview
External Source (WhatsApp / Gmail / etc.)
        ↓
Connector (pure, no side-effects)
        ↓
NormalizedInput + PendingMedia
        ↓
Pipeline (shared)
        ↓
MediaService → saves files
        ↓
Repository → writes to DB