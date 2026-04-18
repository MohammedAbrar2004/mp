# 📌 instruction.md (FOR AI AGENT)

# EchoMind Development Instructions (AI Agent Guide)

---

# 🎯 OBJECTIVE

Build EchoMind as a **modular, decoupled, testable ingestion system**.

We are NOT building everything at once.
We build **one connector at a time**, integrate it with the pipeline, test fully, then move forward.

---

# 🧱 PROJECT SETUP

## Environment

* Python environment name: `mp`
* Database name: `mp`
* Backend path: `mp/backend/`

---

## Step 1 — Virtual Environment

```bash
conda activate mp
```

---

## Step 2 — Database Setup

* PostgreSQL is already installed
* Database `mp` is already created manually

Next steps:

1. Create `schema.sql`
2. Create `init_db.py`
3. Run:

```bash
python app/db/init_db.py
```

---

## Step 3 — Folder Structure

### Root Structure

```text
mp/
├── backend/
├── api/
├── frontend/
```

---

### Backend Structure

```text
backend/
├── app/
│   ├── connectors/
│   ├── db/
│   ├── services/
│   ├── preprocessing/
│   └── api/
│
├── models/
├── pipelines/
├── media/
├── tests/
```

---

### Media Structure

```text
media/
├── audio/
└── documents/
```

---

### API Layer (Node Services)

```text
api/
├── whatsapp/
├── (future: gmail, gmeet, etc.)
```

---

# ⚙️ DEVELOPMENT PHILOSOPHY

* Build **module by module**
* Each connector works **independently**
* No tight coupling between components
* Test everything in isolation before integration

---

# 🔥 CORE DESIGN PRINCIPLES

* Connectors DO NOT write to DB
* Connectors DO NOT save media
* Pipeline handles ALL side-effects
* MediaService handles file storage
* Repository layer handles DB writes
* Database is the single source of truth

---

# 🧩 CORE COMPONENTS

## 1. NormalizedInput

* Universal data contract
* All connectors must return this format

---

## 2. PendingMedia

* Raw media emitted by connectors
* Contains bytes + metadata
* Not yet saved

---

## 3. MediaService

* ONLY component allowed to:

  * write files
  * manage media folders

---

## 4. Pipeline (CRITICAL)

* Single, reusable, connector-agnostic system
* Accepts `List[NormalizedInput]`
* Handles:

  * media saving
  * DB writes

---

# 🔁 SYSTEM DATA FLOW

```text
External Source (WhatsApp / Gmail / etc.)
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
```

---

# 🧠 CONNECTOR RULES (STRICT)

Connectors MUST:

* Return:

  * `NormalizedInput`
  * `PendingMedia` (if media exists)

Connectors MUST NOT:

* write to DB
* save files
* call services
* contain business logic

---

# 🧠 PIPELINE RULES (STRICT)

Pipeline MUST:

* Be reusable for ALL connectors
* Be completely connector-agnostic
* Handle all side-effects

Pipeline MUST NOT:

* contain connector-specific logic
* assume data source
* extract raw data

---

# 🧠 MEDIA RULES

* Connectors → emit `PendingMedia`
* Pipeline → calls `MediaService.save_pending()`
* MediaService → writes files

### Restrictions:

* No `.bin` files allowed
* Must use MIME → extension mapping
* PDFs + Word → `documents/`
* Audio → `audio/`

---

# 🗄️ DATABASE RULES

* Use repository layer ONLY
* No raw SQL inside connectors
* Core tables:

  * `memory_chunks`
  * `media_files`

---

# 🧪 TESTING STRATEGY

For EACH module:

1. Unit Test

   * Test connector independently

2. Integration Test

   * Connector + Pipeline + DB

3. Manual Test

   * Run script + verify DB + files

---

# 🚫 DO NOT

* Couple connectors together
* Mix ingestion with processing
* Save media inside connectors
* Write DB logic inside connectors
* Over-engineer early
* Build scheduler yet

---

# 🔁 DEVELOPMENT SEQUENCE (FINAL)

## Phase 1 — WhatsApp Connector (PURE)

* Real-time ingestion
* Extract messages + media
* Output `NormalizedInput + PendingMedia`

---

## Phase 2 — Core Pipeline (GLOBAL)

* Accept `NormalizedInput`
* Save media via MediaService
* Insert into DB

---

## Phase 3 — WhatsApp End-to-End Test

* Verify:

  * DB entries
  * media files saved
  * correct normalization

---

## Phase 4 — Gmail Connector

* Fetch inbox + sent
* Extract attachments
* Plug into SAME pipeline

---

## Phase 5 — Calendar Connector

* Fetch events
* Normalize structured data
* Plug into SAME pipeline

---

## Phase 6 — Manual Connector

* API-based ingestion
* Accept text + media + metadata

---

## Phase 7 — GMeet Connector

* Fetch recordings/transcripts from Drive
* Store metadata + media
* No processing

---

# 🎯 KEY PRINCIPLE

> Build ONE connector → integrate with pipeline → fully test → move next

NOT:

```text
All connectors → then pipeline ❌
```

---

# 📦 DEPENDENCY MANAGEMENT

We DO NOT manually maintain requirements.txt.

After modules stabilize:

```bash
pip install pipreqs
pipreqs . --force
```

---

# 🎯 CURRENT FOCUS

We are building:

> **Layer 1 (Connectors) + Layer 2 (Ingestion Pipeline)**

Starting with:

1. WhatsApp
2. Gmail
3. Calendar
4. Manual
5. GMeet

---

# 🧭 FINAL INSTRUCTION

Proceed strictly in order:

1. Setup DB
2. Build WhatsApp connector
3. Build pipeline
4. Test end-to-end
5. Move to next connector

No shortcuts. No assumptions.

there is a folder called reference which is strictly for referncing old working code, not copying it.
READ ITS .md file