EchoMind — Preprocessing Layer (Post-Ingestion Enrichment)
🧠 Overview

The preprocessing layer operates after ingestion and prepares raw stored data for semantic understanding.

It transforms:

raw data → structured, clean, meaningful data

This layer does NOT perform semantic reasoning.
It only prepares data for the semantic layer.

🎯 Objectives
Process media into usable text
Clean raw and extracted content
Preserve structure across sources
Assign importance (salience)
Generate embeddings
📦 Input

Data already stored in database:

memory_chunks

Contains:

raw_content
metadata
participants
content_type
timestamps
media_files

Contains:

file paths
mime types
extracted_content (initially NULL)
📤 Output

After preprocessing:

memory_chunks
content → cleaned text
initial_salience → importance score
embedding → vector representation
media_files
extracted_content → raw extracted text
cleaned_content → cleaned text
⚙️ Core Services
1. Media Processing Service
Purpose

Extract text from media files.

Input
media_files.local_path
media_type
mime_type
Output
extracted_content
Supported Types
PDF → text extraction
DOCX → text extraction
Audio → transcription
Behavior
Does NOT clean content
Only extracts raw text
Trigger
is_processed = false
2. Cleaning Service
Purpose

Convert raw content into structured, clean text.

Input
memory_chunks.raw_content
media_files.extracted_content
Output
memory_chunks.content
media_files.cleaned_content
Behavior
Remove noise:
HTML
signatures
formatting artifacts
Normalize:
whitespace
line breaks
Generic cleaning (NOT email-specific)
Model
Local LLM (primary)
Rule-based fallback (optional)
Trigger
is_cleaned = false
3. Salience Service
Purpose

Assign an importance score to each memory.

Input
memory_chunks.content
metadata
presence of media
Output
initial_salience (float: 0 → 1)
Heuristics (initial)
content length
keyword presence
media presence
Trigger
content IS NOT NULL
AND initial_salience IS NULL
4. Embedding Service
Purpose

Convert cleaned content into vector representation.

Input
memory_chunks.content
Output
embedding vector
Model
Local embedding model
Trigger
content IS NOT NULL
AND embedding IS NULL
🔁 Processing Flow
DB (raw data)
   ↓
Media Processing
   ↓
Cleaning Service
   ↓
Salience + Embedding (parallel)
⚠️ Critical Design Decisions
1. No Physical Merge of Media Content
memory_chunks.content ≠ combined content

Instead:

memory_chunks.content → main cleaned text
media_files.cleaned_content → attachment text

Combination happens later at retrieval/semantic stage.

2. Raw Data is Preserved
raw_content is never modified
extracted_content is never overwritten
3. Services are Independent

Each service:

stateless
idempotent
retryable
4. Failure Isolation
One service failure must NOT block others
Failed rows remain retriable
5. Retry Strategy
No retry limits at this stage
Retry policies implemented later
🧠 Database Fields Used
memory_chunks
raw_content
content
is_cleaned
initial_salience
embedding
media_files
extracted_content
cleaned_content
is_cleaned
🚫 Non-Goals

This layer does NOT:

extract entities
detect events
build relationships
modify connectors
modify ingestion pipeline
🔄 Final State After Preprocessing

Each memory becomes:

Raw message/email/event
        ↓
Cleaned content
        ↓
Importance score
        ↓
Vector embedding

Ready for:

Semantic Layer (Layer 3)