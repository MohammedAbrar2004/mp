# 📌 instruction.md (FOR AI AGENT)
EchoMind Development Instructions (AI Agent Guide)
🎯 OBJECTIVE

Build EchoMind as a modular, decoupled, testable ingestion + preprocessing system.

We do NOT build everything at once.
We build layer by layer, fully test, then move forward.

🧱 PROJECT SETUP
Environment
Python environment: mp
Database: mp
Backend path: mp/backend/
Step 1 — Virtual Environment
conda activate mp
Step 2 — Database Setup
PostgreSQL already installed
Database mp already created

Run:

python app/db/init_db.py
Step 3 — Folder Structure
Root
mp/
├── backend/
├── api/
├── frontend/
Backend
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
⚙️ DEVELOPMENT PHILOSOPHY
Build module by module
Keep components decoupled
Test each module independently
Avoid premature complexity
🔥 CORE DESIGN PRINCIPLES
Connectors DO NOT write to DB
Connectors DO NOT save media
Pipeline handles ALL side-effects
Services handle logic
DB is the single source of truth
Raw data must NEVER be modified
🧩 CORE COMPONENTS
1. NormalizedInput
Universal contract
All connectors must return this
2. PendingMedia
Raw media from connectors
Not yet persisted
3. MediaService
Only component allowed to:
save files
manage media directories
4. Ingestion Pipeline
Accepts List[NormalizedInput]
Handles:
media saving
DB writes
deduplication
🔁 SYSTEM DATA FLOW (CURRENT)
External Source
        ↓
Connector (pure)
        ↓
NormalizedInput + PendingMedia
        ↓
Pipeline
        ↓
MediaService
        ↓
Repository → DB write
🧠 CONNECTOR RULES (STRICT)

Connectors MUST:

return NormalizedInput
emit PendingMedia if applicable

Connectors MUST NOT:

write to DB
save files
call services
contain business logic
🧠 PIPELINE RULES (STRICT)

Pipeline MUST:

be connector-agnostic
handle all side-effects

Pipeline MUST NOT:

contain source-specific logic
perform processing/cleaning
🧠 MEDIA RULES
Connectors → emit PendingMedia
Pipeline → calls MediaService
MediaService → saves files

Restrictions:

No .bin files
MIME → extension mapping required
PDFs/DOCX → documents/
Audio → audio/
🗄️ DATABASE RULES
Use repository layer only
No raw SQL in connectors
Core tables:
memory_chunks
media_files
🧪 TESTING STRATEGY

For each module:

Unit Test
Integration Test
Manual verification
🚫 DO NOT
Couple connectors
Mix ingestion with processing
Modify connectors without approval
Over-engineer early
Build scheduler yet
🔁 DEVELOPMENT SEQUENCE (UPDATED)
Phase 1 — Connectors (COMPLETED)
WhatsApp ✔
Gmail ✔
Calendar ✔
Phase 2 — Ingestion Pipeline (COMPLETED)
Media handling ✔
DB writes ✔
Deduplication ✔
Phase 3 — Preprocessing Layer (CURRENT)

This is the next layer after ingestion.

⚙️ PREPROCESSING LAYER RULES (CRITICAL)

This layer operates on:

memory_chunks
media_files
⚠️ CORE PRINCIPLES
Services must be independent
Services must be stateless
Services must be idempotent
Services must be retryable
Failures must NOT cascade
No modification of connectors
🔧 SERVICES TO BUILD
1. Media Processing Service

Input:

media_files.local_path

Output:

extracted_content

Supports:

PDF
DOCX
Audio
2. Cleaning Service

Input:

memory_chunks.raw_content
media_files.extracted_content

Output:

memory_chunks.content
media_files.cleaned_content

Rules:

Generic cleaning (not email-specific)
Use local LLM
3. Salience Service

Input:

cleaned content
metadata
media presence

Output:

initial_salience
4. Embedding Service

Input:

cleaned content

Output:

embedding vector
🔁 PREPROCESSING FLOW
DB (raw)
   ↓
Media Processing
   ↓
Cleaning Service
   ↓
Salience + Embedding (parallel)
⚠️ IMPORTANT DESIGN DECISION
Do NOT merge media into memory_chunks.content

Instead:

memory_chunks.content → main content
media_files.cleaned_content → attachments

Combine only at retrieval / semantic stage.

⚠️ FAILURE STRATEGY
Each service runs independently
Failures are logged
Retry allowed
Retry limits handled later (not now)
⚠️ DATABASE EXTENSIONS

memory_chunks:

content
is_cleaned
initial_salience (nullable)

media_files:

extracted_content
cleaned_content
is_cleaned
📦 DEPENDENCY MANAGEMENT
pip install pipreqs
pipreqs . --force
🎯 CURRENT FOCUS

We are building:

Preprocessing Layer (Post-ingestion)
🧭 FINAL INSTRUCTION

Proceed in order:

Define contracts
Update documentation
Build services one by one
Test each independently
Integrate

No shortcuts. No assumptions.