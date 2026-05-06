## EchoMind (mp) — AI-Powered Cognitive Memory System

# 🧠 Overview

EchoMind is a single-user cognitive memory system designed to passively capture, structure, and recall information from all major communication channels — WhatsApp, Gmail, Calendar, Google Meet, and manual inputs.

The goal is simple but powerful:

You should never lose track of what was said, what was promised, what was scheduled, or what needs to be done.

# ❗ Why This Project Exists

Modern workflows are fragmented:

Conversations happen across WhatsApp, email, meetings
Tasks and commitments get lost in noise
Important context is scattered and unretrievable

Humans are not built to:

remember everything
track conversations across platforms
reconstruct past context accurately

# 🎯 What EchoMind Solves

EchoMind acts as a personal second brain:

Automatically ingests data from multiple sources
Normalizes everything into a unified structure
Stores it in a queryable database
Enables future retrieval like:
“What did I discuss with Amaan last week?”
“What tasks are pending from my project group?”
🏗️ System Vision (Final State)

At full maturity, EchoMind will:

# Layer 1 — Data Ingestion

WhatsApp (real-time, including media)
Gmail (emails + attachments)
Calendar (events)
GMeet (transcripts via Google Drive — planned)
Manual uploads

# Layer 2 — Preprocessing & Storage
Normalize all data into a standard format
Store raw content in database
Store media separately
Process media (PDF, DOCX, audio)
Clean and structure content
Generate embeddings and salience

# Layer 3 — Semantic Understanding (Future)
Extract entities (people, tasks, events)
Build knowledge graph
Link relationships across sources

# Layer 4 — Retrieval Engine (Future)
Query past context intelligently
Combine semantic + temporal search

# Layer 5 — AI Assistant (Future)
Answer questions
Suggest actions
Draft responses


# 📌 CURRENT SYSTEM STATUS

✅ COMPLETED

Data Ingestion Layer
WhatsApp Connector → Complete
Gmail Connector → Complete
Calendar Connector → Complete

Pipeline

NormalizedInput contract → implemented
Ingestion pipeline → stable
MediaService → working
DB writes → stable
Deduplication → enforced via (source_id, external_id)
Database
memory_chunks → storing raw data
media_files → storing media metadata

# 🔄 IN PROGRESS

Preprocessing / Enrichment Layer

This layer operates after ingestion and prepares data for semantic understanding.

⚙️ Preprocessing Layer (Current Work)

# Responsibilities

Media Processing
PDF → text extraction
DOCX → text extraction
Audio → transcription
Cleaning Service
Clean raw_content
Clean media extracted_content
Remove noise (HTML, signatures, formatting)

# Content Structuring
Keep:
memory_chunks.content → cleaned main text
media_files.cleaned_content → cleaned media text
No physical merging
Salience Scoring
Assign importance score to each memory
Embedding Generation
Convert cleaned content into vector embeddings

# Important Design Decision
Media content is NOT merged into memory_chunks.content

Instead:

memory_chunks.content → cleaned primary content
media_files.cleaned_content → per attachment

Combination happens later during retrieval / semantic processing.


# Processing Flow
Raw Ingestion → DB

Then:

media_files → Media Processing → extracted_content
        ↓
Cleaning Service (memory_chunks + media_files)
        ↓
Content ready
        ↓
Salience + Embedding (parallel)
Final State After Preprocessing

Each memory_chunk will have:

raw_content        → original data
content            → cleaned content
initial_salience   → importance score
embedding          → vector representation

# 🧱 Architecture Principles

1. Connectors are Pure

Connectors MUST NOT:

write to DB
save files
contain business logic

2. Pipeline is Central

Handles:

media saving
DB writes
deduplication

3. Raw Data is Preserved
Raw data is NEVER modified

4. Services are Independent

All preprocessing services are:

stateless
idempotent
retryable
failure-isolated

5. Separation of Concerns
Ingestion ≠ Cleaning ≠ Understanding


# 📁 Project Structure

mp/
├── backend/
│   ├── app/
│   │   ├── connectors/
│   │   ├── db/
│   │   ├── services/
│   │   ├── preprocessing/
│   │   └── api/
│   │
│   ├── models/
│   ├── pipelines/
│   ├── media/
│   ├── tests/
│
├── api/
├── frontend/
🗄️ Database
Database: PostgreSQL (mp)

# Tables
1. memory_chunks

Stores:

raw_content
content (cleaned)
metadata
participants
timestamps
salience
embeddings

2. media_files

Stores:

file metadata
extracted_content (raw)
cleaned_content
file paths

# ⚙️ Environment Setup

Inside backend/.env:

DB_HOST=localhost
DB_PORT=5432
DB_NAME=mp
DB_USER=postgres
DB_PASSWORD=your_password

MEDIA_BASE_DIR=./media
RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000


# 🔁 Data Flow Overview
External Source
    ↓
Connector (pure)
    ↓
NormalizedInput + PendingMedia
    ↓
Pipeline
    ↓
MediaService → saves files
    ↓
Repository → writes to DB

--- then ---

DB
    ↓
Preprocessing Layer
    ↓
Semantic Layer (future)


