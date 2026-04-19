# 🧠 EchoMind — Semantic Layer Design

> **Purpose of this document**
> Hand-off spec for building Layer 3 (Semantic Extraction) and the foundations it enables. It defines how EchoMind transitions from raw ingested data → structured meaning → a queryable knowledge graph.
>
> **Intended reader**: the engineer implementing Layer 3 on top of the existing ingestion pipeline.

---

## Table of Contents

1. [Scope & Non-Goals](#1-scope--non-goals)
2. [Required Schema Changes (Read First)](#2-required-schema-changes-read-first)
3. [Core Philosophy](#3-core-philosophy)
4. [Layer Separation](#4-layer-separation)
5. [Data Trust Hierarchy](#5-data-trust-hierarchy)
6. [What We Are Building](#6-what-we-are-building)
7. [Strict Rules (Non-Negotiable)](#7-strict-rules-non-negotiable)
8. [Schema: `memory_chunks`](#8-schema-memory_chunks)
9. [Schema: `media_files`](#9-schema-media_files)
10. [Example Data — `memory_chunks`](#10-example-data--memory_chunks)
11. [Example Data — `media_files`](#11-example-data--media_files)
12. [LLM Usage — Where, Why, How](#12-llm-usage--where-why-how)
13. [Prompt Templates](#13-prompt-templates)
14. [Salience Scoring](#14-salience-scoring)
15. [Schema: `entities`, `events`, Link Tables](#15-schema-entities-events-link-tables)
16. [End-to-End Semantic Pipeline](#16-end-to-end-semantic-pipeline)
17. [Edge Cases, Deduplication & Performance](#17-edge-cases-deduplication--performance)
18. [Final Rules](#18-final-rules)
19. [Implementation Checklist](#19-implementation-checklist)
20. [Recommended Next Steps](#20-recommended-next-steps)

---

## 1. Scope & Non-Goals

### In scope (Layer 3)
- Read `memory_chunks` + `media_files` → produce `entities`, `events`, and their links.
- Content cleaning, salience refinement, LLM-driven extraction, deduplication.
- Traceability from every event back to its originating `memory_chunk`.

### Out of scope (later layers)
- Retrieval / vector search (Layer 4).
- Chat UI, voice UI, agent actions (Layer 5).
- Multi-message session clustering (deferred — see §17.4).

---

## 2. Required Schema Changes (Read First)

Before implementing anything, the database schema needs these additions. The current `CLAUDE.md` schema does not yet include them.

### 2.1 `memory_chunks` — add columns

| Column | Type | Purpose |
|---|---|---|
| `session_id` | `UUID` (nullable) | Reserved for future conversation grouping. Keep nullable. |
| `content` | `TEXT` | Cleaned version of `raw_content`. Semantic layer reads **only** this. |
| `is_cleaned` | `BOOLEAN` | Has `raw_content` been cleaned into `content`? |
| `refined_salience` | `FLOAT` | LLM-refined salience (complements existing `initial_salience`). |

> `raw_content` must remain **untouched** — `content` is a separate, derived column.

### 2.2 `media_files` — add column

| Column | Type | Purpose |
|---|---|---|
| `extracted_content` | `TEXT` | Text extracted from PDF / DOCX / audio. Feeds semantic layer. |

### 2.3 New table — `event_memory_links`

Traceability link between every event and the memory chunk(s) it came from. Critical — without this, events have no provenance.

```sql
CREATE TABLE event_memory_links (
    id              UUID PRIMARY KEY,
    event_id        UUID NOT NULL REFERENCES events(id),
    memory_chunk_id UUID NOT NULL REFERENCES memory_chunks(id),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eml_event ON event_memory_links(event_id);
CREATE INDEX idx_eml_chunk ON event_memory_links(memory_chunk_id);
```

### 2.4 Recommended indexes

```sql
CREATE INDEX idx_memory_chunks_unprocessed
    ON memory_chunks(is_processed, timestamp)
    WHERE is_processed = false;

CREATE INDEX idx_entities_normalized_name ON entities(normalized_name);
CREATE INDEX idx_events_time ON events(event_time);
```

---

## 3. Core Philosophy

> **EchoMind is NOT a chatbot. It is a memory system.**

Each stage has a strict responsibility boundary:

```
Ingestion   ≠   Understanding
Understanding   ≠   Storage
Storage   ≠   Retrieval
```

Violating these boundaries (e.g., putting entity extraction inside a connector) will compound into a fragile system.

---

## 4. Layer Separation

| Layer | Input | Output | Status |
|---|---|---|---|
| **1–2 Ingestion** | Raw source data | `memory_chunks`, `media_files` | ✅ Active |
| **3 Semantic** | `memory_chunks` + `media_files` | `entities`, `events`, links | 🔨 This doc |
| **4 Knowledge Graph / Retrieval** | Structured + vector data | Ranked context | ❌ Not built |
| **5 Response / Agent** | Context + user query | Replies, actions | ❌ Not built |

### Critical design rule

Raw data must **never** be lost or overwritten. This is why `raw_content` and `content` are separate columns.

---

## 5. Data Trust Hierarchy

Not all fields carry equal authority when extracting meaning. Priority:

| Rank | Field | Role |
|---|---|---|
| 🔴 1 | `content` (cleaned) | **Primary source** — all entity/event extraction relies on this |
| 🟡 2 | `metadata` | Supporting context (sender, subject, thread_id) |
| 🟠 3 | `participants` | **Weak signal** — hints only, not facts |
| ⚫ 4 | `raw_content` | Fallback for debugging / reprocessing |

### Why `participants` is weak

```
"+201090536599723"
"GitHub <support@github.com>"
```

These strings are noisy and unreliable as identities.

> **Key insight**
> `participants ≠ entities`
> Instead: `participants → candidate_entities`, `content → confirmed_entities`

---

## 6. What We Are Building

From each `memory_chunk`, extract three things:

### 🧠 Entities — things that exist
- Person → `"Amaan"`
- Organization → `"Google"`
- Project → `"EchoMind"`
- Place → `"New York"`

### 🗓️ Events — things that happen
- `"Meeting at 5pm"`
- `"Project deadline tomorrow"`
- `"Call with client"`

### 🔗 Relationships — how they connect
- `Amaan → participant → Meeting`
- `Google → subject → Email`

### 🔗 Traceability (critical)
Every event links back to the `memory_chunk` it came from, so any extracted fact can be audited against raw data.

---

## 7. Strict Rules (Non-Negotiable)

1. **Do not** extract entities from `participants` directly.
2. **Always** extract from cleaned `content`.
3. **Metadata is supportive, not authoritative.**
4. **Every event must link to a `memory_chunk`** (via `event_memory_links`).
5. **Connectors remain pure** — zero semantic logic inside them.
6. **Cleaning happens before semantic extraction.**

### Note on sessions

`sessions` is a future grouping layer for conversation clustering and multi-message event detection.
- Not implemented now.
- **Not dropped either** — keep the nullable `session_id` column.

---

## 8. Schema: `memory_chunks`

The single source of truth for all ingested memory. Everything in EchoMind starts here.

### 8.1 Final schema (locked)

```sql
CREATE TABLE memory_chunks (
    id                  UUID PRIMARY KEY,
    user_id             UUID NOT NULL,
    source_id           UUID NOT NULL,

    external_message_id TEXT NOT NULL,
    session_id          UUID,                -- nullable, future use

    timestamp           TIMESTAMP NOT NULL,  -- actual event time, not ingestion time

    participants        TEXT[],              -- raw, uncleaned

    content_type        TEXT NOT NULL,       -- text | email | audio | document | gmeet
    raw_content         TEXT,                -- original, never mutated
    content             TEXT,                -- cleaned (LLM-processed)

    embedding           VECTOR(1536),        -- nullable, later

    initial_salience    FLOAT,               -- heuristic
    refined_salience    FLOAT,               -- LLM-based

    is_cleaned          BOOLEAN DEFAULT FALSE,
    is_processed        BOOLEAN DEFAULT FALSE,

    metadata            JSONB,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (source_id, external_message_id)
);
```

### 8.2 Field-by-field purpose

| Field | Purpose |
|---|---|
| `id` | Primary key, referenced by events and media. |
| `user_id` | Single-user now, future multi-user. |
| `source_id` | Which connector generated this memory (WhatsApp, Gmail, etc.). |
| `external_message_id` | Source-side ID. **Critical for deduplication**. |
| `session_id` | Future conversation-grouping key. Keep nullable. |
| `timestamp` | When the event actually happened — not ingestion time. Used for "last week" queries. |
| `participants` | Raw participants from source. Hints only, never trusted as identity. |
| `content_type` | Routing discriminator: `text`, `email`, `document`, `audio`, `gmeet`. |
| `raw_content` | Exact content as received. Never modified. |
| `content` | Cleaned version. **Semantic layer reads this.** |
| `embedding` | 1536-dim vector for later retrieval. |
| `initial_salience` | Heuristic 0–1 importance (length, keywords, names, actions, time). |
| `refined_salience` | LLM-refined 0–1 score. Drives event creation. |
| `is_cleaned` | Has `content` been produced from `raw_content`? |
| `is_processed` | Has the semantic layer already processed this chunk? |
| `metadata` | JSON for per-source context (sender, subject, thread_id, direction). |
| `created_at` | DB insert time. |

### 8.3 Deduplication

Enforced at DB level: `UNIQUE (source_id, external_message_id)`.

---

## 9. Schema: `media_files`

Stores all non-text content linked to `memory_chunks`.

### 9.1 Final schema (locked)

```sql
CREATE TABLE media_files (
    id                 UUID PRIMARY KEY,
    memory_chunk_id    UUID NOT NULL REFERENCES memory_chunks(id),

    original_filename  TEXT,
    media_type         TEXT,          -- document | audio
    mime_type          TEXT,

    local_path         TEXT NOT NULL,
    size_bytes         INT,

    is_processed       BOOLEAN DEFAULT FALSE,

    extracted_content  TEXT,          -- CRITICAL: feeds semantic layer

    metadata           JSONB,

    created_at         TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 9.2 Field purpose

| Field | Purpose |
|---|---|
| `memory_chunk_id` | Parent chunk. One email → N attachments. |
| `original_filename` | As uploaded. |
| `media_type` | `document` or `audio`. |
| `mime_type` | `application/pdf`, `audio/ogg`, etc. |
| `local_path` | Absolute path on disk (written by `MediaService`). |
| `size_bytes` | File size. |
| `is_processed` | Has media been extracted yet? |
| `extracted_content` | **Text extracted from media.** PDF → parsed text. Audio → transcription. Treated identically to `memory_chunks.content` by the semantic layer. |
| `metadata` | Flexible per-file context. |

### 9.3 Relationship

```
memory_chunk (1) ── (N) media_files
```

### 9.4 Design decisions

1. Do **not** store attachment text inside `memory_chunks.raw_content` — keep it in `media_files.extracted_content`.
2. Keep `raw_content` and `content` separate.
3. Media text lives in `extracted_content` only.

---

## 10. Example Data — `memory_chunks`

Thirty realistic rows to calibrate expectations for what "good" ingested data looks like. Assumptions: `content` is cleaned, `participants` is raw, `refined_salience` is placeholder.

### 10.1 WhatsApp — text

| # | external_id | timestamp | content | initial_salience | metadata |
|---|---|---|---|---|---|
| 1 | WA-001 | 2026-04-18 17:00 | "Call me at 5pm" | 0.6 | `{sender, chat_id, is_group:true}` |
| 2 | WA-002 | 2026-04-18 17:02 | "Let's finalize the project deadline tomorrow" | 0.85 | `{sender, chat_id}` |
| 3 | WA-003 | 2026-04-18 17:10 | "Meeting with Amaan at 6pm" | 0.9 | `{sender}` |
| 4 | WA-004 | — | "ok" | 0.1 | — |
| 5 | WA-005 | — | "Did you send the report to Google?" | 0.7 | — |
| 6 | WA-006 | — | "Major Project submission is next week" | 0.95 | — |

### 10.2 WhatsApp — media (content empty; filled via `media_files`)

| # | external_id | content_type | content | initial_salience | metadata |
|---|---|---|---|---|---|
| 7 | WA-DOC-001 | document | `""` | 0.3 | `{message_type:"document"}` |
| 8 | WA-AUDIO-001 | audio | `""` | 0.4 | `{message_type:"audio"}` |

### 10.3 Gmail

| # | external_id | content | initial_salience | metadata |
|---|---|---|---|---|
| 9 | GM-001 | "Please review the attached project report and share feedback." | 0.8 | `{subject:"Project Report", direction:"received", thread_id:"T1"}` |
| 10 | GM-002 | "Meeting scheduled with Google team on Monday at 10 AM." | 0.9 | `{subject:"Meeting Confirmation"}` |
| 11 | GM-003 | "Reminder: Deadline for submission is April 25." | 0.95 | — |
| 12 | GM-004 | "Attached are invoices for last month." | 0.5 | — |
| 13 | GM-005 | "Let's schedule a call with Amaan regarding deployment." | 0.85 | — |
| 14 | GM-006 | "Newsletter content..." | 0.2 | — |

### 10.4 Calendar

| # | external_id | content_type | content | initial_salience |
|---|---|---|---|---|
| 15 | CAL-001 | gmeet | "Team meeting at 5 PM regarding project updates" | 0.9 |
| 16 | CAL-002 | gmeet | "Doctor appointment at 3 PM" | 0.7 |
| 17 | CAL-003 | gmeet | "Hackathon event next Saturday" | 0.8 |

### 10.5 Manual

| # | external_id | content | initial_salience |
|---|---|---|---|
| 18 | MAN-001 | "Prepare slides for AI presentation" | 0.9 |
| 19 | MAN-002 | "Buy groceries" | 0.2 |

### 10.6 Mixed follow-ups

| # | source | external_id | content | initial_salience |
|---|---|---|---|---|
| 20 | whatsapp | WA-010 | "Amaan confirmed the meeting at 7pm" | 0.9 |
| 21 | gmail | GM-010 | "Google approved the proposal" | 0.85 |
| 22 | whatsapp | WA-011 | "Let's meet at cafe near college" | 0.6 |
| 23 | whatsapp | WA-012 | "Send the updated doc ASAP" | 0.75 |
| 24 | gmail | GM-011 | "Deployment scheduled for Friday" | 0.9 |
| 25 | manual | MAN-010 | "Study for exam" | 0.5 |
| 26 | whatsapp | WA-013 | "Deadline extended by 2 days" | 0.85 |
| 27 | gmail | GM-012 | "Invitation: Project Review Meeting" | 0.8 |
| 28 | whatsapp | WA-014 | "ok noted" | 0.1 |
| 29 | calendar | CAL-010 | "Client call at 11 AM" | 0.85 |
| 30 | manual | MAN-020 | "Call Amaan regarding project" | 0.9 |

### 10.7 Observations

- 🔴 Not every row becomes an event — `"ok"`, `"Newsletter"`, `"Buy groceries"` stay as chunks only.
- 🟢 High-salience rows drive meaning — `"Meeting at 5pm"`, `"Deadline tomorrow"`, `"Call Amaan"`.
- 🟡 Entities live inside `content`, not `participants`.
- 🔵 Media rows have empty `content` — meaning arrives via `media_files.extracted_content`.

---

## 11. Example Data — `media_files`

Thirty linked rows showing how attachments become first-class semantic input.

> **Rule**
> Semantic layer must read `memory_chunks.content` **and** `media_files.extracted_content` together.

### 11.1 Documents (PDF / DOCX)

| # | memory_chunk | filename | extracted_content |
|---|---|---|---|
| 1 | 7 | project_report.pdf | "Project Report: EchoMind system architecture, connectors, semantic layer design, and database schema." |
| 2 | 7 | timeline.pdf | "Project timeline: Phase 1 ingestion complete, Phase 2 semantic extraction pending." |
| 3 | 9 | meeting_notes.pdf | "Meeting Notes: Discussed deadline extension and responsibilities assigned to Amaan and team." |
| 4 | 12 | invoice_april.pdf | "Invoice for April: Amount due 15,000 INR, payable before May 5." |
| 5 | 12 | invoice_march.pdf | "Invoice for March: Paid successfully." |
| 6 | 20 | proposal.docx | "Proposal approved by Google. Next step is deployment phase." |
| 7 | 23 | updated_document.docx | "Updated project documentation with revised architecture and API endpoints." |
| 8 | 24 | deployment_plan.pdf | "Deployment scheduled Friday at 10 AM. Requires server readiness." |
| 9 | 30 | task_list.docx | "Tasks: Call Amaan, finalize UI, prepare presentation." |

### 11.2 Audio (voice notes → transcription)

| # | memory_chunk | filename | extracted_content |
|---|---|---|---|
| 10 | 8 | voice_note_1.ogg | "Hey, let's meet tomorrow at 6 PM near college." |
| 11 | 8 | voice_note_2.ogg | "I spoke to Amaan, he confirmed the meeting." |
| 12 | 20 | voice_note_3.ogg | "The deadline has been pushed by two days." |
| 13 | 26 | voice_note_4.ogg | "Deployment is scheduled for Friday." |
| 14 | 21 | voice_note_5.ogg | "Google approved the proposal." |

### 11.3 Email attachments

| # | memory_chunk | filename | extracted_content |
|---|---|---|---|
| 15 | 9 | report.pdf | "Please review the report and share feedback." |
| 16 | 10 | agenda.pdf | "Agenda: Meeting with Google team at 10 AM." |
| 17 | 13 | deployment_notes.pdf | "Deployment requires final approval from Amaan." |
| 18 | 27 | invitation.pdf | "Invitation: Project Review Meeting scheduled Friday." |

### 11.4 More documents & extras

| # | memory_chunk | filename | extracted_content |
|---|---|---|---|
| 19 | 18 | presentation.pptx | "AI presentation slides covering semantic memory system." |
| 20 | 18 | notes.txt | "Prepare slides and rehearse before presentation." |
| 21 | 25 | study_material.pdf | "Exam syllabus includes machine learning and NLP." |
| 22 | 29 | client_notes.pdf | "Client expects delivery by Friday." |
| 23 | 29 | contract.pdf | "Contract signed for project execution." |
| 24 | 6 | deadline_doc.pdf | "Major Project submission due next week." |
| 25 | 2 | deadline_plan.pdf | "Finalize deadline tomorrow." |
| 26 | 3 | voice_note_6.ogg | "Meeting with Amaan at 6 PM." |
| 27 | 22 | location_info.pdf | "Meeting location: Cafe near college." |
| 28 | 24 | server_details.pdf | "Server setup required before deployment." |
| 29 | 21 | approval_doc.pdf | "Proposal officially approved." |
| 30 | 30 | call_notes.txt | "Discuss project updates with Amaan." |

### 11.5 Observations

- 🔴 Media carries high value — reports, deadlines, confirmations live in attachments.
- 🟢 `extracted_content` is semantic input, treated identically to `content`.
- 🟡 One memory can have many media rows.
- 🔵 Audio becomes text via transcription before entering the pipeline.

### 11.6 How the semantic layer uses this

```text
combined_text =
    memory_chunk.content
    + "\n"
    + (all extracted_content from linked media_files)
```

#### Example

```text
Email content:     "Please review the report"
Attachment text:   "Project deadline is April 25"

combined_text:     "Please review the report.
                    Project deadline is April 25"

Event detected:    "Project deadline — April 25"
```

### 11.7 Rules

1. Always merge media `extracted_content` into the main content before extraction.
2. Do not treat media as a separate extraction pass.
3. Skip media with empty `extracted_content`.
4. Mark media `is_processed = true` after extraction.

---

## 12. LLM Usage — Where, Why, How

> **First principle**
> The LLM is **not** your system. It is a **tool inside** your system.

### 12.1 Where NOT to use LLMs ❌

- Connectors
- Ingestion pipeline
- Deduplication
- Media storage
- Raw DB writes

These must stay deterministic, fast, and reliable.

### 12.2 Where LLMs are used ✅

#### 1. Content cleaning (pre-semantic)

Raw data is messy — emails contain HTML and signatures, audio transcription leaves artifacts, docs have formatting junk. The LLM turns `raw_content` into `content`: readable, structured, concise, meaning-preserving.

```text
Input:   "Hi team,<br><br>Please review the attached report.<br>Regards,<br>John<br>Unsubscribe..."
Output:  "Please review the attached report and share feedback."
```

#### 2. Entity extraction

```text
Input:   "Meeting with Amaan at Google office tomorrow"
Output:
[
  {"name": "Amaan",  "type": "person"},
  {"name": "Google", "type": "organization"}
]
```

#### 3. Event detection

```text
Input:   "Deadline is April 25"
Output:
{
  "title": "Project deadline",
  "time":  "2026-04-25",
  "type":  "deadline"
}
```

#### 4. Relationship extraction

```text
Input:   "Amaan confirmed the meeting"
Output:
{
  "entity": "Amaan",
  "role":   "participant",
  "event":  "meeting"
}
```

#### 5. Salience refinement

```text
Input:   "ok"                              → 0.05
Input:   "Final deadline is tomorrow"      → 0.95
```

### 12.3 Summary

| Task | Purpose |
|---|---|
| Cleaning | Structure text |
| Entities | Extract objects |
| Events | Detect actions |
| Relationships | Connect objects |
| Salience | Prioritize importance |

### 12.4 Trust but verify

LLMs hallucinate entities and events. Always ground outputs in the input text:

```python
if entity_name.lower() not in combined_text.lower():
    discard(entity)
```

### 12.5 Cost optimization

- ❌ Bad: run the LLM on every message.
- ✅ Correct: heuristic filter first → LLM only on high-salience chunks.

---

## 13. Prompt Templates

### Prompt design rules

1. Output must be strict JSON.
2. No explanations, only structured data.
3. Stay grounded in the input text.

### 13.1 Cleaning

```text
Clean the following text by removing noise, signatures, HTML, and irrelevant content.
Preserve meaning.
Return ONLY the cleaned text.

TEXT:
{raw_content}
```

### 13.2 Entity extraction

```text
Extract entities from the text.
Return JSON:
[
  {"name": "...", "type": "person|organization|place|project"}
]

TEXT:
{content}
```

### 13.3 Event detection

```text
Identify meaningful events in the text.
Return JSON:
[
  {
    "title": "...",
    "time":  "...",
    "type":  "meeting|deadline|call|task"
  }
]

TEXT:
{content}
```

### 13.4 Relationship extraction

```text
Link entities to events.
Return JSON:
[
  {
    "entity": "...",
    "event":  "...",
    "role":   "participant|organizer|subject"
  }
]

TEXT:
{content}
```

### 13.5 Salience

```text
Rate the importance of this message from 0 to 1.
Consider: urgency, decisions, deadlines, actions.
Return ONLY a number.

TEXT:
{content}
```

---

## 14. Salience Scoring

> **Salience = how important a memory is.**
> Without it, every message becomes an event and the system becomes useless.
> With it, only meaningful content becomes structured knowledge.

### 14.1 Two-level system (locked)

```
initial_salience  → fast heuristic
refined_salience  → LLM refinement
```

### 14.2 Initial salience (heuristic)

Fast filter applied **before** calling any LLM.

**Factors**

| Factor | Signal |
|---|---|
| Message length | Longer → more likely meaningful |
| Keywords | `meeting`, `deadline`, `call`, `submit`, `review`, `confirm`, `schedule` |
| Named mentions | Presence of names raises the score |
| Action verbs | `send`, `review`, `call`, `complete` |
| Time indicators | `tomorrow`, `5pm`, `Friday` |

**Formula (simple and effective)**

```
score =
    0.30 * length_score
  + 0.25 * keyword_score
  + 0.20 * entity_presence
  + 0.15 * action_score
  + 0.10 * time_score
```

Normalize to `[0, 1]`.

**Worked example**

```text
Input: "Meeting with Amaan at 5pm"

length   → 0.7
keyword  → 1.0
entity   → 1.0
action   → 0.6
time     → 1.0

initial_salience ≈ 0.87
```

### 14.3 Thresholds (non-negotiable)

| Range | Action |
|---|---|
| `< 0.3` | 🔴 Ignore completely (`"ok"`, `"hmm"`, `"lol"`) |
| `0.3 – 0.6` | 🟡 Candidate — keep chunk, no LLM yet |
| `> 0.6` | 🟢 Strong signal — send to LLM for refinement |

### 14.4 Refined salience (LLM)

LLM evaluates urgency, decisions, commitments, outcomes — things heuristics miss, e.g., `"Let's wrap this up"` (important but no keywords).

Output: float in `[0, 1]`.

### 14.5 Event creation rule

| `refined_salience` | Action |
|---|---|
| `> 0.7` | ✅ Create event |
| `0.5 – 0.7` | ⚠️ Optional event (context-dependent) |
| `< 0.5` | ❌ Do not create event |

### 14.6 Full flow

```
memory_chunk
    ↓
initial_salience (fast)
    ↓
if > 0.6 → LLM
    ↓
refined_salience
    ↓
if > 0.7 → create event
```

### 14.7 Rules

1. Never run the LLM on low-salience messages.
2. Salience is a cost-optimization gate, not just a ranking.
3. Events come only from high-salience chunks.
4. Salience is per `memory_chunk`, not per entity.

### 14.8 Real examples

| # | Text | initial | refined | Outcome |
|---|---|---|---|---|
| ❌ | `"ok"` | 0.10 | — | Ignored |
| 🟡 | `"Send the doc"` | 0.50 | 0.60 | No event |
| 🟢 | `"Meeting with Amaan at 5pm"` | 0.85 | 0.92 | Event created |
| 🟢 | `"Deadline is April 25"` | 0.90 | 0.95 | Event created |

---

## 15. Schema: `entities`, `events`, Link Tables

> **Core principle**
> Nothing exists in the graph without a `memory_chunk`. This is the ground-truth guarantee.

### 15.1 `entities`

```sql
CREATE TABLE entities (
    id               UUID PRIMARY KEY,

    name             TEXT NOT NULL,
    type             TEXT NOT NULL,           -- person | organization | place | project

    normalized_name  TEXT NOT NULL,           -- lowercase, trimmed — for dedup

    mention_count    INT  NOT NULL DEFAULT 1,

    first_seen       TIMESTAMP,
    last_seen        TIMESTAMP,

    salience_score   FLOAT,                   -- overall importance

    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Key fields**

| Field | Purpose |
|---|---|
| `name` | Display form: `"Amaan"`, `"Google"`, `"EchoMind"`. |
| `type` | `person`, `organization`, `place`, `project`. |
| `normalized_name` | `"amaan"`, `"google"`, `"echomind"`. **Used for deduplication.** |
| `mention_count` | Increments instead of creating duplicates. |
| `salience_score` | Aggregate importance across mentions. |

**Rules**

1. Entities must be deduplicated.
2. The same entity must not exist twice.
3. Update `mention_count` instead of inserting new rows.

### 15.2 `events`

```sql
CREATE TABLE events (
    id              UUID PRIMARY KEY,

    title           TEXT NOT NULL,
    event_type      TEXT NOT NULL,     -- meeting | deadline | call | task

    event_time      TIMESTAMP,         -- nullable

    salience_score  FLOAT,

    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Rules**

1. Events are only created when `refined_salience > 0.7`.
2. Events must be meaningful — not chatter.

### 15.3 `entity_event_links`

```sql
CREATE TABLE entity_event_links (
    id          UUID PRIMARY KEY,

    entity_id   UUID NOT NULL REFERENCES entities(id),
    event_id    UUID NOT NULL REFERENCES events(id),

    role        TEXT NOT NULL,   -- participant | organizer | subject | mentioned

    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Role values (strict)**: `participant`, `organizer`, `subject`, `mentioned`.

**Example**

```
Amaan  → participant → Meeting
Google → subject     → Proposal
```

### 15.4 `event_memory_links` (traceability — critical)

```sql
CREATE TABLE event_memory_links (
    id                UUID PRIMARY KEY,

    event_id          UUID NOT NULL REFERENCES events(id),
    memory_chunk_id   UUID NOT NULL REFERENCES memory_chunks(id),

    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Every extracted event points back to its originating chunk. Without this, events become unauditable claims.

### 15.5 Full relationship graph

```
memory_chunks
    ↓
(event_memory_links)
    ↓
events
    ↓
(entity_event_links)
    ↓
entities
```

### 15.6 Design rules

1. Every event **must** link to a `memory_chunk`.
2. Entities never exist without context.
3. Do not create events for low-salience data.
4. Deduplicate entities aggressively.

### 15.7 End-to-end example

**Input**

```
"Meeting with Amaan at 5pm"
```

**Output**

```text
entities:
  - Amaan (person)

events:
  - Meeting at 5pm

entity_event_links:
  - Amaan → participant → Meeting

event_memory_links:
  - Meeting → memory_chunk #42
```

### 15.8 Entity deduplication (must-have)

**Problem**

```
"Amaan"
"amaan"
"Amaan Khan"
```

**Solution**: `normalized_name` + fuzzy matching (see §17.1).

### 15.9 Explicitly deferred: `sessions`

Not implemented now, not dropped. Used later for conversation grouping and multi-message reasoning. Keep the nullable `session_id` in `memory_chunks`.

---

## 16. End-to-End Semantic Pipeline

### 16.1 Big picture

```
memory_chunks + media_files
         ↓
   semantic pipeline
         ↓
entities / events / links
```

### 16.2 Core rule

Process each `memory_chunk` independently. No global reasoning yet — that is a future step.

### 16.3 Full flow

```
1.  Fetch unprocessed memory_chunks
2.  Clean content (if needed)
3.  Merge media extracted_content
4.  Compute initial_salience
5.  Filter low-salience
6.  Run LLM (selectively)
7.  Extract entities
8.  Detect events
9.  Upsert entities (with dedup)
10. Link entities ↔ events
11. Link event  ↔ memory_chunk
12. Mark processed
```

### 16.4 Step-by-step

#### Step 1 — Fetch

```sql
SELECT *
FROM memory_chunks
WHERE is_processed = FALSE
ORDER BY timestamp ASC
LIMIT N;
```

#### Step 2 — Ensure cleaned content

```python
if not chunk.is_cleaned:
    chunk.content = clean_with_llm(chunk.raw_content)
    chunk.is_cleaned = True
```

#### Step 3 — Merge media content

```python
media = get_media(chunk.id)
combined_text = chunk.content or ""

for m in media:
    if m.extracted_content:
        combined_text += "\n" + m.extracted_content
```

#### Step 4 — Initial salience

```python
chunk.initial_salience = compute_heuristic_score(combined_text)
```

#### Step 5 — Filter

```python
if chunk.initial_salience < 0.3:
    mark_processed(chunk)
    continue
```

#### Step 6 — LLM refinement

```python
if chunk.initial_salience > 0.6:
    chunk.refined_salience = llm_salience(combined_text)
else:
    chunk.refined_salience = chunk.initial_salience
```

#### Step 7 — Entity extraction

```python
entities = llm_extract_entities(combined_text)
```

#### Step 8 — Event detection

```python
if chunk.refined_salience > 0.7:
    events = llm_detect_events(combined_text)
else:
    events = []
```

#### Step 9 — Upsert entities

```python
for e in entities:
    existing = find_by_normalized_name(normalize(e.name))
    if existing:
        existing.mention_count += 1
        existing.last_seen = chunk.timestamp
        update(existing)
    else:
        create_entity(e, first_seen=chunk.timestamp)
```

#### Step 10 — Create events

```python
for ev in events:
    event_id = insert_event(ev, salience=chunk.refined_salience)
```

#### Step 11 — Link entities ↔ events

```python
relations = llm_relationships(combined_text)
for r in relations:
    link_entity_event(r.entity, r.event, r.role)
```

#### Step 12 — Link event ↔ memory (traceability)

```python
for ev in events:
    create_event_memory_link(ev.id, chunk.id)
```

#### Step 13 — Finalize

```python
chunk.is_processed = True
update(chunk)
```

### 16.5 Full pseudocode

```python
def semantic_pipeline():
    chunks = fetch_unprocessed_chunks()

    for chunk in chunks:

        # 1. Cleaning
        if not chunk.is_cleaned:
            chunk.content = clean_with_llm(chunk.raw_content)
            chunk.is_cleaned = True

        # 2. Merge media
        combined_text = chunk.content or ""
        for m in get_media(chunk.id):
            if m.extracted_content:
                combined_text += "\n" + m.extracted_content

        # 3. Salience
        chunk.initial_salience = heuristic_score(combined_text)
        if chunk.initial_salience < 0.3:
            mark_processed(chunk)
            continue

        # 4. Refine
        if chunk.initial_salience > 0.6:
            chunk.refined_salience = llm_salience(combined_text)
        else:
            chunk.refined_salience = chunk.initial_salience

        # 5. Entities
        entities = llm_extract_entities(combined_text)

        # 6. Events
        events = (
            llm_detect_events(combined_text)
            if chunk.refined_salience > 0.7
            else []
        )

        # 7. Upsert entities
        for e in entities:
            upsert_entity(e, chunk.timestamp)

        # 8. Create events
        event_ids = [
            create_event(ev, chunk.refined_salience)
            for ev in events
        ]

        # 9. Relationships
        for r in llm_relationships(combined_text):
            link_entity_event(r)

        # 10. Traceability
        for eid in event_ids:
            link_event_memory(eid, chunk.id)

        # 11. Finalize
        mark_processed(chunk)
```

### 16.6 Implementation rules

1. Never reprocess chunks where `is_processed = true`.
2. Never skip `event_memory_links`.
3. Never overwrite `raw_content`.
4. Always merge media before extraction.
5. Entity dedup happens **before** insert.

### 16.7 Failure cases and fixes

| Case | Fix |
|---|---|
| Duplicate entities | `normalized_name` + fuzzy matching |
| Noisy events | Raise salience threshold |
| Missing events | Improve LLM prompts |
| High cost | Tighten heuristic filter |

### 16.8 Output per chunk

After processing one chunk:
- ✔ Entities upserted
- ✔ Events created (if important)
- ✔ Relationships linked
- ✔ Traceability stored
- ✔ Chunk marked processed

---

## 17. Edge Cases, Deduplication & Performance

### 17.1 Entity deduplication (critical)

**Problem**

```
"Amaan"
"amaan"
"Amaan Khan"
"amaan khan"
```

Without handling: duplicate rows → fragmented graph → bad queries.

**Multi-step solution**

1. **Normalize** — `normalized_name = lowercase(trim(name))`.
2. **Exact match** — `WHERE normalized_name = ?`.
3. **Fuzzy match** — Levenshtein or trigram similarity. Threshold: `similarity > 0.85` → same entity.
4. **Merge strategy** — on match: increment `mention_count`, update `last_seen`, optionally update `salience_score`.

> **Rule**: never create duplicate entities.

### 17.2 Event deduplication

**Problem**: `"Meeting at 5pm"` vs `"Meeting confirmed at 5pm"`.

**Dedup key**: `(title, event_time)`.

```python
existing = find_event(title, time)
if existing:
    reuse(existing.id)
else:
    create_new()
```

### 17.3 Partial / weak messages

`"ok"`, `"done"`, `"yes"` → `initial_salience < 0.3` → skipped entirely.

### 17.4 Multi-message events

**Problem**

```
msg1: "meeting?"
msg2: "5pm works"
msg3: "confirmed"
```

**Current limitation**: we process one chunk at a time.
**Future solution**: `sessions` table to group chunks. Not implemented now, but do not ignore the need.

### 17.5 Media without extracted content

If `extracted_content` is empty → skip that media entry.

### 17.6 LLM hallucinations

Validate every output against the source text:

```python
if entity_name.lower() not in combined_text.lower():
    discard(entity)
```

### 17.7 Missing or relative timestamps

Resolve relative time using `chunk.timestamp`:

```
"tomorrow" + chunk.timestamp(2026-04-18) → 2026-04-19
```

### 17.8 Data consistency rules

1. Every event **must** have an `event_memory_link`.
2. Every entity must have at least one mention.
3. No orphan events.
4. No duplicate entities.
5. No processing without cleaned content.

### 17.9 Performance strategy

- **Heuristic filter first** — only high-salience chunks reach the LLM.
- **Batch processing** — e.g., 50 chunks per pass.
- **Indexes** — `normalized_name`, `timestamp`, `source_id`, partial index on `is_processed = false`.
- **Async** — semantic layer runs as a background job, never blocks ingestion.

### 17.10 Failure recovery

On crash, `is_processed = false` chunks are picked up again next run. Consider a `failed_jobs` entry after N retries.

### 17.11 Growth strategy

- Archive old chunks once retrieval layer is live.
- Compress embeddings later if needed.

### 17.12 Logging (required)

Track: ingestion errors, LLM failures, entity conflicts, event creation counts per run.

### 17.13 Summary

- ✔ Deduplicate entities aggressively
- ✔ Deduplicate events carefully
- ✔ Skip low-value data
- ✔ Validate LLM outputs
- ✔ Maintain traceability
- ✔ Optimize LLM usage
- ✔ Prepare for scale

---

## 18. Final Rules

These are non-negotiable. Breaking them will degrade the system.

### 18.1 Data integrity

1. `raw_content` is **never** modified.
2. `content` is **always** derived from `raw_content`.
3. Every `memory_chunk` is processed at most once.
4. Every event **must** link to a `memory_chunk`.
5. No orphan entities or events.

### 18.2 Semantic

6. Entities are extracted **only** from `content` — never from `participants`.
7. Participants are hints only.
8. Metadata is supportive, not authoritative.
9. `media_files.extracted_content` **must** be merged into `content` before extraction.
10. LLM outputs must be grounded in the text.

### 18.3 Salience

11. `initial_salience < 0.3` → ignore.
12. `initial_salience > 0.6` → LLM processing.
13. `refined_salience > 0.7` → event creation.
14. No event without sufficient salience.

### 18.4 Deduplication

15. Entities: `normalized_name` + fuzzy match.
16. Events: `(title, time)`.
17. Always update existing rows instead of inserting duplicates.

### 18.5 Architecture

18. Connectors remain pure — zero semantic logic.
19. Ingestion layer remains deterministic.
20. Semantic layer is the **only** place meaning is created.
21. Media processing is separate from ingestion.

### 18.6 Performance

22. Never run the LLM on low-salience data.
23. Batch process.
24. Background only — never blocking ingestion.

---

## 19. Implementation Checklist

### Phase 1 — Schema prep
- [ ] Add `session_id`, `content`, `is_cleaned`, `refined_salience` to `memory_chunks`.
- [ ] Add `extracted_content` to `media_files`.
- [ ] Create `event_memory_links` table.
- [ ] Add indexes: `normalized_name`, `timestamp`, partial index on `is_processed = false`.

### Phase 2 — Preprocessing
- [ ] Cleaning service implemented (LLM or rule-based).
- [ ] `is_cleaned` flag handled correctly.
- [ ] Media extraction pipeline ready (PDF / DOCX / audio → text).

### Phase 3 — Salience
- [ ] Heuristic scoring function.
- [ ] Keyword list defined.
- [ ] Thresholds enforced in pipeline.

### Phase 4 — Semantic extraction
- [ ] Entity extraction.
- [ ] Event detection.
- [ ] Relationship extraction.
- [ ] LLM prompts finalized (see §13).

### Phase 5 — Graph construction
- [ ] Entity upsert with dedup (exact + fuzzy).
- [ ] Event creation with `(title, time)` dedup.
- [ ] `entity_event_links` population.
- [ ] `event_memory_links` population.

### Phase 6 — Pipeline control
- [ ] `is_processed` flag correctly flipped.
- [ ] Retry mechanism for failures.
- [ ] Logging: errors, LLM failures, counts per run.

### Verification — your responsibility
- [ ] No duplicate entities in the DB.
- [ ] No meaningless events created.
- [ ] Media content is actually used.
- [ ] Salience filtering is working (spot-check).
- [ ] LLM outputs are grounded in text.
- [ ] Relationships make logical sense.

---

## 20. Recommended Next Steps

Two viable paths:

| Option | Action |
|---|---|
| **A** (recommended) | Build Calendar connector first, then start Layer 3. More diverse data → better semantic design. |
| **B** | Start Layer 3 immediately on existing Gmail + WhatsApp data. |

Reasoning: more varied ingestion surfaces edge cases in the semantic layer early, before too much code depends on narrow assumptions.

---

## Closing

If this document is followed strictly, EchoMind becomes a real cognitive memory system rather than a toy project. The hard part is the discipline — not the code.

- ✔ Clean ingestion system
- ✔ Multi-source data
- ✔ Structured design
- ✔ Clear semantic pipeline
- ✔ Defined rules