# EchoMind — Preprocessing Contracts

1. OVERVIEW

This document defines strict contracts for the preprocessing (post-ingestion enrichment) layer.

This layer operates on data already stored in:

memory_chunks
media_files

It prepares data for the semantic layer.

2. CORE PRINCIPLES

All services MUST follow:

Stateless
Idempotent
Independently retryable
Failure-isolated

3. GLOBAL DATA FLOW
Raw DB Data
    ↓
Media Processing
    ↓
Cleaning Service
    ↓
Salience + Embedding (parallel)

4. DATABASE CONTRACT
memory_chunks (relevant fields)

Input (existing):

id
raw_content
content_type
metadata
participants

Output (to be filled):

content
is_cleaned
initial_salience
embedding
media_files (relevant fields)

Input:

id
memory_chunk_id
local_path
media_type
mime_type

Output:

extracted_content
cleaned_content
is_cleaned

5. SERVICE CONTRACTS
5.1 MEDIA PROCESSING SERVICE
Purpose

Extract raw text from media files.

Input
media_files row:
id
local_path
media_type
mime_type
Output
extracted_content (TEXT)
Supported Types
document → PDF, DOCX
audio → voice notes
Behavior
Extract raw text only
DO NOT clean
DO NOT modify memory_chunks
Trigger Condition
media_files.extracted_content IS NULL
Failure Handling
Log failure
Leave extracted_content NULL
Allow retry
Idempotency Rule
If extracted_content exists → skip

5.2 CLEANING SERVICE
Purpose

Convert raw text into clean, structured content.

Input

From memory_chunks:

raw_content
content_type
metadata

From media_files:

extracted_content
Output

memory_chunks:

content
is_cleaned = true

media_files:

cleaned_content
is_cleaned = true
Behavior
Remove:
HTML
signatures
formatting noise
Normalize:
whitespace
structure
Generic cleaning (not email-specific)
Model
Primary → local LLM
Fallback → rule-based cleaning
Trigger Conditions

For memory_chunks:

is_cleaned = false

For media_files:

is_cleaned = false AND extracted_content IS NOT NULL
Failure Handling
Log error
Keep is_cleaned = false
Allow retry
Idempotency Rule
If is_cleaned = true → skip

5.3 SALIENCE SERVICE
Purpose

Assign an importance score to each memory.

Input
memory_chunks.content
metadata
media presence (exists in media_files)
Output
initial_salience (FLOAT 0–1)
Behavior (Initial Heuristics)
content length
keyword presence
media presence
Trigger Condition
content IS NOT NULL
AND initial_salience IS NULL
Failure Handling
Leave initial_salience NULL
Allow retry
Idempotency Rule
If initial_salience exists → skip

5.4 EMBEDDING SERVICE
Purpose

Generate vector embeddings from cleaned content.

Input
memory_chunks.content
Output
embedding vector
Model
Local embedding model
Trigger Condition
content IS NOT NULL
AND embedding IS NULL
Failure Handling
Leave embedding NULL
Allow retry
Idempotency Rule
If embedding exists → skip

6. ORCHESTRATION CONTRACT

Execution Order
1. Media Processing
2. Cleaning Service
3. Salience + Embedding (parallel)

Rules
Services must NOT call each other directly
Orchestrator controls execution
Each service can run independently

7. MERGE STRATEGY (IMPORTANT)

There is NO physical merge of media into memory_chunks.

memory_chunks.content → main cleaned text
media_files.cleaned_content → attachment text

Combination happens at:

retrieval layer
semantic processing

8. RETRY STRATEGY
Each service scans for incomplete rows
No global transaction required
Failures do NOT block pipeline
Future (not now):
retry limits
failure marking

9. NON-GOALS

This layer does NOT:

extract entities
build relationships
perform semantic reasoning
modify ingestion pipeline
modify connectors

10. FINAL OUTPUT STATE

Each memory_chunk will have:

raw_content
content
initial_salience
embedding

Each media_file will have:

extracted_content
cleaned_content

11. GUARANTEES

After preprocessing:

Data is clean
Data is structured
Data is ready for semantic layer