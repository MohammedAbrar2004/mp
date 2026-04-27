"""
Synthetic data seed script for EchoMind.

Before running:
  1. Review the MEDIA MANIFEST printed below.
  2. Create each listed file and place it in the correct folder:
       backend/media/documents/  (PDFs and DOCX)
       backend/media/audio/      (OGG files)
  3. Run from backend/:  python seed_synthetic_data.py

MEDIA MANIFEST
==============

PDFs (backend/media/documents/):
  report_1.pdf
    EchoMind Major Project – Architecture Overview
    EchoMind is a personal memory assistant that ingests data from WhatsApp,
    Gmail, Google Meet, and manual inputs. The system is built on a layered
    pipeline: ingestion, preprocessing, and semantic enrichment. The ingestion
    layer normalises all inputs into a common schema. The preprocessing layer
    cleans text and extracts content from media files. The semantic layer
    computes embeddings and salience scores to rank memories. The tech stack
    includes Python, FastAPI, PostgreSQL with pgvector, and Ollama for local LLM
    inference. The project is being developed as a major project submission by
    Abrar, Amaan, and Abdullah under the guidance of Ma'am.

  report_2.pdf
    EchoMind – Preprocessing Layer Design
    The preprocessing pipeline processes each memory chunk in three steps.
    First, media extraction: PDFs and DOCX files are parsed to extract raw text.
    Audio files are transcribed using Whisper medium model. Second, content
    cleaning: the extracted text is sent to a local Mistral 7B model via Ollama
    for cleaning and normalisation. The cleaning prompt strips noise, corrects
    formatting, and returns a cleaned version. Third, salience scoring: an
    embedding is computed for each chunk using a sentence-transformer model and
    stored in the pgvector column. An initial salience score is assigned based
    on content length and keyword density.

  report_3.pdf
    EchoMind – Database Schema Notes
    The core tables are users, data_sources, memory_chunks, and media_files.
    memory_chunks stores one row per message or event with fields for raw
    content, cleaned content, embedding vector, and salience scores. media_files
    stores one row per attached file, linked to its parent memory chunk by
    foreign key. The schema uses UUIDs for all primary keys and JSONB for
    flexible metadata storage. Indexes are defined on source_id, timestamp, and
    the embedding vector column for fast retrieval.

  report_4.pdf
    EchoMind – Connector Layer Summary
    Four connectors are implemented. The WhatsApp connector receives push
    messages via a webhook and handles text, document, and audio message types.
    The Gmail connector polls the Gmail API on a schedule and converts emails
    into normalised inputs. The Google Meet connector extracts transcripts from
    Meet recordings stored in Google Drive. The Calendar connector fetches
    upcoming and past events from Google Calendar. A manual connector allows
    direct text input through a CLI or API endpoint. All connectors output
    NormalizedInput objects that are passed to the ingestion pipeline.

  report_5.pdf
    EchoMind – Testing and Validation Plan
    Unit tests cover the connector normalisation logic and the preprocessing
    services individually. Integration tests run the full pipeline from
    NormalizedInput to database insertion and verify that memory chunks are
    created with the correct content type and participant data. The preprocessing
    tests check that PDF extraction returns non-empty text, that the LLM cleaner
    returns a shortened cleaned version, and that embeddings have the correct
    dimension. End-to-end tests will be added before the final presentation to
    verify that semantic queries return relevant results.

  report_6.pdf
    EchoMind – Presentation Outline
    Slide 1: Problem statement – information overload, fragmented memory across
    apps. Slide 2: Solution – EchoMind as a unified personal memory layer.
    Slide 3: System architecture diagram. Slide 4: Ingestion pipeline walkthrough.
    Slide 5: Preprocessing and LLM cleaning demo. Slide 6: Semantic search demo.
    Slide 7: Future roadmap – fine-tuning, mobile app, multi-user support.
    Slide 8: Conclusion and Q&A.

  report_7.pdf
    EchoMind – Risk Register
    Risk 1: Ollama local LLM latency during live demo. Mitigation: pre-run
    preprocessing before presentation. Risk 2: WhatsApp webhook unavailable.
    Mitigation: use saved connector output as fallback. Risk 3: Database
    connection failure on presentation machine. Mitigation: test on lab machine
    24 hours in advance. Risk 4: Large media files causing memory errors.
    Mitigation: restrict demo files to under 5MB and avoid scanned PDFs.

  report_8.pdf
    EchoMind – Meeting Minutes 2026-04-22
    Attendees: Abrar, Amaan, Abdullah, Ma'am.
    Agenda: mid-project review.
    Points discussed: ingestion pipeline is complete and tested. Preprocessing
    layer is functional but LLM cleaning is slow for large inputs. Semantic
    layer is partially complete – embeddings are being stored but salience
    scoring needs calibration. Ma'am asked for a working demo by 2026-04-28.
    Action items: Abrar to fix participant mapping in WhatsApp connector. Amaan
    to tune salience thresholds. Abdullah to complete the semantic query API.
    Next meeting: 2026-04-25 at 11:00 AM.

  report_9.pdf
    EchoMind – API Endpoint Specification
    POST /ingest: accepts a JSON body with source_type and content fields.
    Returns the created memory_chunk_id on success.
    GET /chunks: returns a paginated list of memory chunks for the current user.
    Supports filtering by content_type and date range.
    POST /search: accepts a query string and returns the top-k semantically
    similar memory chunks ranked by cosine similarity and salience score.
    GET /media/{chunk_id}: returns metadata and local path for media files
    attached to a given memory chunk.
    All endpoints require the user_id header for single-user prototype mode.

  report_10.pdf
    EchoMind – Deployment Notes
    The backend runs as a single Python process using Uvicorn and FastAPI.
    PostgreSQL with the pgvector extension must be installed and running locally.
    Ollama must be running on localhost:11434 with the mistral:7b-instruct-q4_0
    model pulled. The WhatsApp webhook requires a public URL; ngrok is used
    during development. Environment variables: DATABASE_URL, MEDIA_BASE_DIR,
    OLLAMA_URL. The seed script populates the users and data_sources tables.
    Run migrations before seeding: psql -f app/db/schema.sql.

  report_11.pdf
    EchoMind – Semantic Layer Design
    The semantic layer runs after preprocessing is complete. For each cleaned
    memory chunk, a sentence-transformer model computes a 1536-dimensional
    embedding vector. The vector is stored in the pgvector column. An initial
    salience score is assigned using a heuristic based on content length,
    presence of action keywords, and participant count. Chunks with salience
    above a threshold receive additional enrichment: a title, summary, and
    keyword list are generated using the local LLM. These fields are stored in
    the memory_chunks table and used to improve search result presentation.

  report_12.pdf
EchoMind – Known Issues and Workarounds
Issue 1: participant mapping for WhatsApp uses JID format which does not
match Gmail email addresses. Workaround: maintain a manual mapping table.
Issue 2: Whisper transcription forces output to English even for Urdu audio.
This is intentional for the MVP but should be made configurable later.
Issue 3: LLM cleaning truncates input at 2000 characters. Long documents
are partially cleaned. Workaround: for the demo use documents under 2000
characters. Issue 4: Calendar events without descriptions produce empty
raw_content. Workaround: use event title as fallback content.

DOCX (backend/media/documents/):
  notes_1.docx
    Sprint Planning Notes – Day 1
    Tasks assigned: Abrar handles WhatsApp connector and ingestion pipeline.
    Amaan handles Gmail connector and preprocessing layer. Abdullah handles
    semantic layer and database schema. Target: have connectors working by
    end of Day 2. Preprocessing to be completed by Day 4. Semantic layer by
    Day 6. Final integration and testing on Day 7. Ma'am to be updated every
    two days with progress reports.

  notes_2.docx
    EchoMind Feature Checklist
    [x] WhatsApp connector – text messages
    [x] WhatsApp connector – document messages with caption
    [x] WhatsApp connector – audio messages
    [x] Gmail connector – email ingestion
    [x] Calendar connector – event ingestion
    [x] Manual connector – direct text input
    [x] Ingestion pipeline – media saving and DB insertion
    [x] Preprocessing – PDF text extraction
    [x] Preprocessing – DOCX text extraction
    [x] Preprocessing – audio transcription via Whisper
    [ ] Semantic layer – salience calibration
    [ ] Semantic layer – search API endpoint
    [ ] End-to-end integration test

  notes_3.docx
    Hadi's Feedback on EchoMind Demo
    Hadi saw the early demo and said the concept is solid. He suggested adding
    a simple web UI so non-technical users can query their memories. He also
    pointed out that the search results need better ranking – right now they
    come back unordered. He liked the WhatsApp integration the most because it
    felt immediately useful. He suggested demoing it with real messages to make
    the presentation more compelling. He also asked if it can search across
    multiple sources at once, like finding all mentions of a deadline across
    WhatsApp and email. That would be a strong demo moment.

  notes_4.docx
    Pre-Presentation Checklist
    1. Run schema migration on lab machine.
    2. Run seed script to populate database with demo data.
    3. Start Ollama service and confirm mistral model is loaded.
    4. Start PostgreSQL and confirm pgvector extension is active.
    5. Run preprocessing pipeline to clean all chunks.
    6. Run semantic layer to compute embeddings.
    7. Test search query: "EchoMind architecture" – expect report_1 in results.
    8. Test search query: "meeting with Ma'am" – expect meeting minutes chunk.
    9. Confirm WhatsApp webhook is live via ngrok.
    10. Charge laptop, arrive 30 minutes early.

  notes_5.docx
    Abdullah's Database Optimisation Notes
    Added index on memory_chunks.timestamp for chronological queries.
    Added index on memory_chunks.source_id for per-source filtering.
    The pgvector HNSW index on the embedding column improves approximate
    nearest-neighbour search speed significantly compared to exact scan.
    JSONB participants column allows flexible querying with GIN index.
    Considered partitioning memory_chunks by source_id but decided against it
    for the MVP since row count is small. Will revisit if the table grows past
    one million rows.

  notes_6.docx
    Amaan's Preprocessing Notes
    The LLM cleaning step is the bottleneck. Mistral 7B takes 3-8 seconds per
    chunk on CPU. For the demo database of 100 chunks this means up to 13
    minutes of preprocessing time. Options: run preprocessing overnight before
    the presentation, or skip LLM cleaning and rely on heuristic cleaning only.
    For the MVP the heuristic cleaner removes page numbers, headers, and
    repeated whitespace which is sufficient for the demo. LLM cleaning adds
    value for real-world noisy data but is not critical for the presentation.

  notes_7.docx
Abrar's WhatsApp Connector Notes
The connector receives messages via a webhook POST endpoint. Media bytes
are attached to the message object under the _file_bytes key. The connector
checks for documentMessage, audioMessage, and documentWithCaptionMessage
types. Caption text is used as the raw_content. For text messages the
message body is used directly. The JID format for participants is
91XXXXXXXXXX@s.whatsapp.net for individuals and XXXXXXXXXX@g.us for groups.
Participant mapping to human-readable names is done using the pushName field
in the message object.

  notes_8.docx
    Project Timeline – EchoMind MVP
    Week 1: Requirements gathering, architecture design, DB schema.
    Week 2: WhatsApp and Gmail connector implementation.
    Week 3: Ingestion pipeline and media handling.
    Week 4: Preprocessing layer – extraction and LLM cleaning.
    Week 5: Semantic layer – embeddings and salience scoring.
    Week 6: Integration, testing, and bug fixes.
    Week 7: Demo data preparation and presentation rehearsal.
    Submission deadline: 2026-04-28. Presentation slot: 2026-04-29 at 10:00 AM.

  notes_9.docx
    Ma'am Review Feedback – 2026-04-22
    Ma'am reviewed the mid-project demo and gave the following feedback.
    Positive: the architecture is well-structured and the ingestion pipeline
    works reliably. The WhatsApp integration is impressive for a student project.
    Areas for improvement: the search results need to be presented more clearly.
    The salience scoring is not yet visible in the demo – should be shown as a
    score next to each result. The README needs to be updated to include setup
    instructions. Ma'am also asked us to add a short video demo as a backup
    in case the live demo fails.

  notes_10.docx
    Semantic Search Query Examples
    Query: "what did we discuss in the last meeting"
    Expected: meeting minutes chunk from 2026-04-22
    Query: "EchoMind deployment steps"
    Expected: deployment notes and pre-presentation checklist
    Query: "WhatsApp connector issues"
    Expected: Abrar's connector notes and known issues document
    Query: "Ma'am feedback"
    Expected: Ma'am review feedback and meeting minutes
    Query: "deadline"
    Expected: project timeline, pre-presentation checklist, calendar events
    These queries will be used during the live demo to demonstrate semantic
    search capability across all ingested sources.

  notes_11.docx
    EchoMind – What We Learned
    Building EchoMind taught us several things. First, normalising data from
    different sources is harder than it looks – each source has its own quirks.
    Second, local LLM inference is slow but private and free, which matters for
    a personal memory assistant. Third, vector search is powerful but needs good
    embeddings to work well – garbage in, garbage out. Fourth, the preprocessing
    step is critical: raw WhatsApp messages are noisy and need cleaning before
    they are useful for search. Fifth, building incrementally and testing each
    layer before moving to the next saved us a lot of debugging time.

  notes_12.docx
    Post-Submission Plan
    After submission we plan to continue developing EchoMind. Priority features:
    multi-user support with proper authentication, a web UI for querying memories,
    mobile app integration, and support for image and video media types.
    Longer term: fine-tuning a small LLM on personal data for better relevance,
    integration with Notion and Slack, and an automated daily summary feature
    that surfaces the most important memories from the past 24 hours. We also
    want to open-source the project after cleaning up the codebase.

Audio (backend/media/audio/):
  voice_1.ogg
    Script: Hey Amaan, just checking if you've pushed the preprocessing changes.
    Ma'am wants a quick update by tonight.

  voice_2.ogg
    Script: Abdullah, the pgvector index is causing an issue on my machine.
    Can you share the exact command you used to create it?

  voice_3.ogg
    Script: Guys the demo is looking really good. I think we're ready.
    Just need to sort out the search ranking before Thursday.

  voice_4.ogg
    Script: Abrar, I finished the Gmail connector. Tested it with ten emails
    and it's ingesting correctly. You can pull the latest branch.

  voice_5.ogg
    Script: Quick reminder, we have a meeting with Ma'am tomorrow at 11.
    Make sure the demo is running before we go in.

  voice_6.ogg
    Script: The Whisper transcription works but it's slow on CPU.
    I'm thinking we pre-process all audio the night before the presentation.

  voice_7.ogg
    Script: Abdullah told me the embedding dimension is 1536.
    Make sure the pgvector column matches otherwise the insert will fail.

  voice_8.ogg
    Script: Hadi was asking if EchoMind can search old WhatsApp messages.
    That's literally the whole point, I told him yes.

  voice_9.ogg
    Script: I just realised we forgot to handle the case where a WhatsApp
    message has media but no caption. Abrar, can you fix that?

  voice_10.ogg
    Script: Everything is working end to end now. Ingestion, preprocessing,
    semantic layer, all good. Let's do a full run tonight and check the DB.

==============
END OF MANIFEST
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from typing import List

from models.normalized_input import NormalizedInput, PendingMedia
from pipelines.ingestion_pipeline import process


def _d(day: int, hour: int, minute: int = 0) -> datetime:
    days = [20, 21, 22, 23, 24, 25, 26]
    return datetime(2026, 4, days[day - 1], hour, minute, tzinfo=timezone.utc)


def _read(filename: str, folder: str) -> bytes:
    path = os.path.join("media", folder, filename)
    with open(path, "rb") as f:
        return f.read()


def _pdf(filename: str, captured_at: datetime) -> PendingMedia:
    return PendingMedia(
        raw_bytes=_read(filename, "documents"),
        original_filename=filename,
        mime_type="application/pdf",
        captured_at=captured_at,
    )


def _docx(filename: str, captured_at: datetime) -> PendingMedia:
    return PendingMedia(
        raw_bytes=_read(filename, "documents"),
        original_filename=filename,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        captured_at=captured_at,
    )


def _ogg(filename: str, captured_at: datetime) -> PendingMedia:
    return PendingMedia(
        raw_bytes=_read(filename, "audio"),
        original_filename=filename,
        mime_type="audio/ogg",
        captured_at=captured_at,
    )


WA_ALL = ["918888888888@wa", "919999999999@wa", "917777777777@wa"]
WA_AB_AM = ["918888888888@wa", "919999999999@wa"]
WA_AB_AD = ["918888888888@wa", "917777777777@wa"]
WA_AM_AD = ["919999999999@wa", "917777777777@wa"]

inputs: List[NormalizedInput] = [

    # ── WHATSAPP (40) ──────────────────────────────────────────────────────────

    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_1",
        content="Guys let's finalise the architecture today. I've drafted something, sending it now.",
        content_type="text", event_time=_d(1, 9, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_2",
        content="Check this architecture overview. Let me know if anything's missing.",
        content_type="document", event_time=_d(1, 9, 5),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar", "caption": "Check this architecture overview. Let me know if anything's missing."},
        media=[_pdf("report_1.pdf", _d(1, 9, 5))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_3",
        content="Looks good to me. The layered pipeline makes sense.",
        content_type="text", event_time=_d(1, 9, 15),
        participants=WA_AB_AM, metadata={"chat": "group", "sender": "Amaan"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_4",
        content="Same. Abdullah, you handle the DB schema right?",
        content_type="text", event_time=_d(1, 9, 17),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_5",
        content="Yeah I'll do schema and semantic layer.",
        content_type="text", event_time=_d(1, 9, 20),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abdullah"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_6",
        content="Ok so Abrar does WhatsApp connector + ingestion, I do Gmail + preprocessing, Abdullah does semantic + DB. Let's go.",
        content_type="text", event_time=_d(1, 9, 25),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_7",
        content="Here are my sprint notes for reference.",
        content_type="document", event_time=_d(1, 10, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar", "caption": "Here are my sprint notes for reference."},
        media=[_docx("notes_1.docx", _d(1, 10, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_9",
        content="Hey Amaan, just checking if you've pushed the preprocessing changes. Ma'am wants a quick update by tonight.",
        content_type="audio", event_time=_d(2, 8, 30),
        participants=WA_AB_AM, metadata={"chat": "dm", "sender": "Abrar"},
        media=[_ogg("voice_1.ogg", _d(2, 8, 30))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_10",
        content="Yeah pushed it an hour ago. Check the preprocessing branch.",
        content_type="text", event_time=_d(2, 8, 45),
        participants=WA_AB_AM, metadata={"chat": "dm", "sender": "Amaan"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_11",
        content="Preprocessing design doc is here, have a look before the meeting.",
        content_type="document", event_time=_d(2, 9, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan", "caption": "Preprocessing design doc is here, have a look before the meeting."},
        media=[_pdf("report_2.pdf", _d(2, 9, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_12",
        content="Abdullah, the pgvector index is causing an issue on my machine. Can you share the exact command you used to create it?",
        content_type="audio", event_time=_d(2, 10, 0),
        participants=WA_AB_AD, metadata={"chat": "dm", "sender": "Abrar"},
        media=[_ogg("voice_2.ogg", _d(2, 10, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_13",
        content="CREATE INDEX ON memory_chunks USING hnsw (embedding vector_cosine_ops);  — make sure pgvector extension is enabled first.",
        content_type="text", event_time=_d(2, 10, 15),
        participants=WA_AB_AD, metadata={"chat": "dm", "sender": "Abdullah"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_14",
        content="My DB notes are in this doc if it helps.",
        content_type="document", event_time=_d(2, 10, 20),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abdullah", "caption": "My DB notes are in this doc if it helps."},
        media=[_pdf("report_3.pdf", _d(2, 10, 20))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_16",
        content="Connector summary doc – shows what each connector does and what it returns.",
        content_type="document", event_time=_d(2, 14, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar", "caption": "Connector summary doc – shows what each connector does and what it returns."},
        media=[_pdf("report_4.pdf", _d(2, 14, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_17",
        content="Guys the demo is looking really good. I think we're ready. Just need to sort out the search ranking before Thursday.",
        content_type="audio", event_time=_d(2, 16, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan"},
        media=[_ogg("voice_3.ogg", _d(2, 16, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_18",
        content="Abrar, I finished the Gmail connector. Tested it with ten emails and it's ingesting correctly. You can pull the latest branch.",
        content_type="audio", event_time=_d(3, 9, 0),
        participants=WA_AB_AM, metadata={"chat": "dm", "sender": "Amaan"},
        media=[_ogg("voice_4.ogg", _d(3, 9, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_19",
        content="pulled, looks clean",
        content_type="text", event_time=_d(3, 9, 20),
        participants=WA_AB_AM, metadata={"chat": "dm", "sender": "Abrar"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_20",
        content="Quick reminder, we have a meeting with Ma'am tomorrow at 11. Make sure the demo is running before we go in.",
        content_type="audio", event_time=_d(3, 10, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar"},
        media=[_ogg("voice_5.ogg", _d(3, 10, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_21",
        content="API spec doc – endpoints we need to build for the semantic query layer.",
        content_type="document", event_time=_d(3, 11, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abdullah", "caption": "API spec doc – endpoints we need to build for the semantic query layer."},
        media=[_pdf("report_9.pdf", _d(3, 11, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_22",
        content="The Whisper transcription works but it's slow on CPU. I'm thinking we pre-process all audio the night before the presentation.",
        content_type="audio", event_time=_d(3, 14, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan"},
        media=[_ogg("voice_6.ogg", _d(3, 14, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_23",
        content="Agreed. Let's run preprocessing overnight on Day 6.",
        content_type="text", event_time=_d(3, 14, 10),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_24",
        content="Meeting minutes from today attached.",
        content_type="document", event_time=_d(4, 12, 30),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar", "caption": "Meeting minutes from today attached."},
        media=[_pdf("report_8.pdf", _d(4, 12, 30))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_25",
        content="Abdullah told me the embedding dimension is 1536. Make sure the pgvector column matches otherwise the insert will fail.",
        content_type="audio", event_time=_d(4, 13, 0),
        participants=WA_AB_AM, metadata={"chat": "dm", "sender": "Abrar"},
        media=[_ogg("voice_7.ogg", _d(4, 13, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_26",
        content="Yeah the schema already has VECTOR(1536). Should be fine.",
        content_type="text", event_time=_d(4, 13, 15),
        participants=WA_AB_AM, metadata={"chat": "dm", "sender": "Amaan"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_27",
        content="Hadi was asking if EchoMind can search old WhatsApp messages. That's literally the whole point, I told him yes.",
        content_type="audio", event_time=_d(4, 15, 0),
        participants=WA_AB_AM, metadata={"chat": "dm", "sender": "Abrar"},
        media=[_ogg("voice_8.ogg", _d(4, 15, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_29",
        content="I just realised we forgot to handle the case where a WhatsApp message has media but no caption. Abrar, can you fix that?",
        content_type="audio", event_time=_d(5, 9, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan"},
        media=[_ogg("voice_9.ogg", _d(5, 9, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_30",
        content="on it",
        content_type="text", event_time=_d(5, 9, 10),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_31",
        content="Fixed. Empty caption now falls back to empty string, no crash.",
        content_type="text", event_time=_d(5, 10, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_32",
        content="Ma'am feedback from the meeting. Important – read before Thursday.",
        content_type="document", event_time=_d(5, 11, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar", "caption": "Ma'am feedback from the meeting. Important – read before Thursday."},
        media=[_docx("notes_9.docx", _d(5, 11, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_33",
        content="Known issues doc. Abdullah added some workarounds, good to know before the demo.",
        content_type="document", event_time=_d(5, 14, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan", "caption": "Known issues doc. Abdullah added some workarounds, good to know before the demo."},
        media=[_pdf("report_12.pdf", _d(5, 14, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_34",
        content="Everything is working end to end now. Ingestion, preprocessing, semantic layer, all good. Let's do a full run tonight and check the DB.",
        content_type="audio", event_time=_d(6, 9, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abdullah"},
        media=[_ogg("voice_10.ogg", _d(6, 9, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_35",
        content="Full run done. All 100 chunks ingested, preprocessing completed. Embeddings look correct.",
        content_type="text", event_time=_d(6, 23, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_36",
        content="Pre-presentation checklist. Go through it tonight.",
        content_type="document", event_time=_d(6, 23, 30),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan", "caption": "Pre-presentation checklist. Go through it tonight."},
        media=[_docx("notes_4.docx", _d(6, 23, 30))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_37",
        content="👍",
        content_type="text", event_time=_d(6, 23, 35),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abdullah"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_38",
        content="Deployment notes in case anything breaks on the lab machine.",
        content_type="document", event_time=_d(7, 7, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar", "caption": "Deployment notes in case anything breaks on the lab machine."},
        media=[_pdf("report_10.pdf", _d(7, 7, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_39",
        content="All set. See you guys at the lab at 9:30.",
        content_type="text", event_time=_d(7, 8, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan"},
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_40",
        content="good luck everyone",
        content_type="text", event_time=_d(7, 8, 5),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abdullah"},
    ),

    # ── GMAIL (25) ────────────────────────────────────────────────────────────

    NormalizedInput(
        source_type="gmail", external_id="gmail_1",
        content="Subject: EchoMind – Initial Task Assignment\n\nHi team,\n\nQuick summary of what we agreed today. Abrar: WhatsApp connector and ingestion pipeline. Amaan: Gmail connector and preprocessing. Abdullah: database schema and semantic layer. Let's aim to have connectors working by end of Day 2. Reply if anything is unclear.\n\nBest,\nAbrar\n\n--\nAbrar Farooq | EchoMind Project\nabrar@gmail.com",
        content_type="email", event_time=_d(1, 11, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "abrar@gmail.com", "to": ["amaan@gmail.com", "abdullah@gmail.com"], "subject": "EchoMind – Initial Task Assignment"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_2",
        content="Subject: Re: EchoMind – Initial Task Assignment\n\nGot it. I'll start with the Gmail API setup today and move to preprocessing once the connector is working.\n\n– Amaan\n\nOn Mon, Apr 20, 2026 at 11:00 AM Abrar <abrar@gmail.com> wrote:\n\n> Hi team,\n>\n> Quick summary of what we agreed today. Abrar: WhatsApp connector and\n> ingestion pipeline. Amaan: Gmail connector and preprocessing. Abdullah:\n> database schema and semantic layer. Let's aim to have connectors\n> working by end of Day 2.\n>\n> Best,\n> Abrar",
        content_type="email", event_time=_d(1, 11, 30),
        participants=["amaan@gmail.com", "abrar@gmail.com"],
        metadata={"from": "amaan@gmail.com", "to": ["abrar@gmail.com"], "subject": "Re: EchoMind – Initial Task Assignment"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_3",
        content="Subject: Re: EchoMind – Initial Task Assignment\n\nSame here. Schema draft will be ready by tonight. I'll push it to the repo.\n\n– Abdullah\n\nOn Mon, Apr 20, 2026 at 11:00 AM Abrar <abrar@gmail.com> wrote:\n\n> Hi team,\n>\n> Quick summary of what we agreed today. Abrar: WhatsApp connector and\n> ingestion pipeline. Amaan: Gmail connector and preprocessing. Abdullah:\n> database schema and semantic layer.\n>\n> Best,\n> Abrar",
        content_type="email", event_time=_d(1, 12, 0),
        participants=["abdullah@gmail.com", "abrar@gmail.com"],
        metadata={"from": "abdullah@gmail.com", "to": ["abrar@gmail.com"], "subject": "Re: EchoMind – Initial Task Assignment"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_4",
        content="Subject: EchoMind – Progress Update for Ma'am\n\nDear Ma'am,\n\nHere is our Day 1 progress update for EchoMind. We have finalised the system architecture and divided tasks among team members. The database schema is drafted. WhatsApp connector skeleton is in place. We expect to have working connectors by Day 2. Please let us know if you have any early feedback.\n\nRegards,\nAbrar, Amaan, Abdullah\n\n--\nEchoMind Major Project\nBatch 2024-25 | Computer Science",
        content_type="email", event_time=_d(1, 18, 0),
        participants=["abrar@gmail.com", "maam@university.edu"],
        metadata={"from": "abrar@gmail.com", "to": ["maam@university.edu"], "cc": ["amaan@gmail.com", "abdullah@gmail.com"], "subject": "EchoMind – Progress Update for Ma'am"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_5",
        content="Subject: Re: EchoMind – Progress Update for Ma'am\n\nGood start. Make sure the architecture document is finalised before the mid-review. I will check your repository before our meeting on Day 3. Please also prepare a short demo showing at least one connector working end to end.\n\nRegards,\nMa'am\n\nOn Mon, Apr 20, 2026 at 6:00 PM Abrar <abrar@gmail.com> wrote:\n\n> Dear Ma'am,\n>\n> Here is our Day 1 progress update for EchoMind. We have finalised the\n> system architecture and divided tasks. The database schema is drafted.\n> WhatsApp connector skeleton is in place.\n>\n> Regards,\n> Abrar, Amaan, Abdullah",
        content_type="email", event_time=_d(1, 20, 0),
        participants=["maam@university.edu", "abrar@gmail.com"],
        metadata={"from": "maam@university.edu", "to": ["abrar@gmail.com"], "subject": "Re: EchoMind – Progress Update for Ma'am"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_6",
        content="Subject: WhatsApp Connector – End to End Working\n\nHi Amaan and Abdullah,\n\nThe WhatsApp connector is now working end to end. Text messages, documents with captions, and audio messages are all being ingested correctly. Media files are saved to disk and linked to their memory chunks. I've pushed to the whatsapp-connector branch. Please review when you get a chance.\n\nAbrar\n\n--\nAbrar Farooq\nabrar@gmail.com",
        content_type="email", event_time=_d(2, 15, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "abrar@gmail.com", "to": ["amaan@gmail.com", "abdullah@gmail.com"], "subject": "WhatsApp Connector – End to End Working"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_7",
        content="Subject: Preprocessing Layer – Status\n\nHi Abrar,\n\nPreprocessing is about 80% done. PDF extraction via pypdf is working. DOCX extraction is working. Audio transcription via Whisper is working but slow on CPU. LLM cleaning via Ollama is working but I've had to cap input at 2000 characters due to timeout issues. Will complete the pipeline orchestrator today.\n\nAmaan\n\n--\nAmaan | EchoMind Project\namaan@gmail.com",
        content_type="email", event_time=_d(2, 17, 0),
        participants=["amaan@gmail.com", "abrar@gmail.com"],
        metadata={"from": "amaan@gmail.com", "to": ["abrar@gmail.com"], "subject": "Preprocessing Layer – Status"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_8",
        content="Subject: Database Schema Pushed\n\nHi team,\n\nI've pushed the final schema to the repo. Key tables: users, data_sources, memory_chunks, media_files. The pgvector extension is required. Run the schema file with psql before starting the app. I've also added the seed script for the prototype user and data sources. Let me know if you hit any issues.\n\nAbdullah\n\n--\nAbdullah | EchoMind Project\nabdullah@gmail.com",
        content_type="email", event_time=_d(2, 19, 0),
        participants=["abdullah@gmail.com", "abrar@gmail.com", "amaan@gmail.com"],
        metadata={"from": "abdullah@gmail.com", "to": ["abrar@gmail.com", "amaan@gmail.com"], "subject": "Database Schema Pushed"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_9",
        content="Subject: Meeting Confirmation – Day 3 at 11:00 AM\n\nDear Ma'am,\n\nConfirming our meeting tomorrow, Day 3, at 11:00 AM in your office. We will have a live demo of the WhatsApp connector and the ingestion pipeline. We will also walk through the architecture document.\n\nRegards,\nAbrar\n\n--\nAbrar Farooq\nabrar@gmail.com",
        content_type="email", event_time=_d(2, 20, 0),
        participants=["abrar@gmail.com", "maam@university.edu"],
        metadata={"from": "abrar@gmail.com", "to": ["maam@university.edu"], "subject": "Meeting Confirmation – Day 3 at 11:00 AM"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_10",
        content="Subject: Re: Meeting Confirmation – Day 3 at 11:00 AM\n\nConfirmed. Please bring printed copies of your architecture diagram.\n\nMa'am\n\nOn Tue, Apr 21, 2026 at 8:00 PM Abrar <abrar@gmail.com> wrote:\n\n> Dear Ma'am,\n>\n> Confirming our meeting tomorrow at 11:00 AM in your office. We will\n> have a live demo of the WhatsApp connector and the ingestion pipeline.\n>\n> Regards,\n> Abrar",
        content_type="email", event_time=_d(2, 20, 30),
        participants=["maam@university.edu", "abrar@gmail.com"],
        metadata={"from": "maam@university.edu", "to": ["abrar@gmail.com"], "subject": "Re: Meeting Confirmation – Day 3 at 11:00 AM"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_11",
        content="Subject: Post-Meeting Summary – Day 3\n\nHi team,\n\nKey takeaways from today's meeting with Ma'am. She wants a working demo by Day 7. Salience scoring needs to be visible in the demo UI. Search results should show scores. She also asked for a video demo as backup. Action items are in the meeting minutes document. Let's regroup on Day 5 to check progress.\n\nAbrar\n\n--\nAbrar Farooq\nabrar@gmail.com",
        content_type="email", event_time=_d(3, 13, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "abrar@gmail.com", "to": ["amaan@gmail.com", "abdullah@gmail.com"], "subject": "Post-Meeting Summary – Day 3"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_12",
        content="Subject: Semantic Layer – Embeddings Working\n\nHi Abrar,\n\nEmbeddings are now being computed and stored in the pgvector column. I'm using a 1536-dim model. Cosine similarity search is working via pgvector. Salience scoring is partially done – initial scores are assigned but the enrichment step (title/summary/keywords) is still in progress. Should be complete by Day 5.\n\nAbdullah\n\n--\nAbdullah | EchoMind Project\nabdullah@gmail.com",
        content_type="email", event_time=_d(4, 10, 0),
        participants=["abdullah@gmail.com", "abrar@gmail.com"],
        metadata={"from": "abdullah@gmail.com", "to": ["abrar@gmail.com"], "subject": "Semantic Layer – Embeddings Working"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_13",
        content="Subject: Hadi's Feedback\n\nHi guys,\n\nShared the demo with Hadi. His main feedback: add a web UI, improve search ranking, and demo cross-source search (finding a deadline mentioned in both WhatsApp and email). I've written up his full feedback in a DOCX file, sharing on WhatsApp. Good input for the post-submission roadmap.\n\nAbrar\n\n--\nAbrar Farooq\nabrar@gmail.com",
        content_type="email", event_time=_d(4, 16, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "abrar@gmail.com", "to": ["amaan@gmail.com", "abdullah@gmail.com"], "subject": "Hadi's Feedback"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_14",
        content="Subject: Testing Plan Document\n\nHi team,\n\nAttaching the testing plan. Please review before Day 6 so we can run through all test cases together.\n\nAmaan\n\n--\nAmaan | EchoMind Project\namaan@gmail.com",
        content_type="email", event_time=_d(4, 17, 0),
        participants=["amaan@gmail.com", "abrar@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "amaan@gmail.com", "to": ["abrar@gmail.com", "abdullah@gmail.com"], "subject": "Testing Plan Document"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_15",
        content="Subject: Risk Register\n\nHi team,\n\nI've put together a risk register for the presentation. Main risks: Ollama latency, WhatsApp webhook going down, DB connection failure on lab machine. Mitigations are documented. Please read before Day 7.\n\nAbdullah\n\n--\nAbdullah | EchoMind Project\nabdullah@gmail.com",
        content_type="email", event_time=_d(5, 9, 0),
        participants=["abdullah@gmail.com", "abrar@gmail.com", "amaan@gmail.com"],
        metadata={"from": "abdullah@gmail.com", "to": ["abrar@gmail.com", "amaan@gmail.com"], "subject": "Risk Register"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_16",
        content="Subject: Day 5 Progress Update for Ma'am\n\nDear Ma'am,\n\nDay 5 update. Ingestion pipeline: complete. Preprocessing: complete. Semantic layer: embeddings working, salience calibration in progress. We are on track for the Day 7 demo. We will send the final demo query list tomorrow for your review.\n\nRegards,\nAbrar\n\n--\nAbrar Farooq\nEchoMind Major Project\nabrar@gmail.com",
        content_type="email", event_time=_d(5, 18, 0),
        participants=["abrar@gmail.com", "maam@university.edu"],
        metadata={"from": "abrar@gmail.com", "to": ["maam@university.edu"], "subject": "Day 5 Progress Update for Ma'am"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_17",
        content="Subject: Re: Day 5 Progress Update for Ma'am\n\nThank you for the update. Please ensure the salience scores are visible in the demo. I will be watching that specifically. Good luck.\n\nRegards,\nMa'am\n\nOn Fri, Apr 24, 2026 at 6:00 PM Abrar <abrar@gmail.com> wrote:\n\n> Dear Ma'am,\n>\n> Day 5 update. Ingestion pipeline: complete. Preprocessing: complete.\n> Semantic layer: embeddings working, salience calibration in progress.\n> We are on track for the Day 7 demo.\n>\n> Regards,\n> Abrar",
        content_type="email", event_time=_d(5, 19, 0),
        participants=["maam@university.edu", "abrar@gmail.com"],
        metadata={"from": "maam@university.edu", "to": ["abrar@gmail.com"], "subject": "Re: Day 5 Progress Update for Ma'am"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_18",
        content="Subject: Semantic Search Query Examples\n\nHi team,\n\nHere are the ten demo queries we'll run during the presentation. I've also written the expected results for each. We should test all of these before Day 7.\n\nAbdullah\n\n--\nAbdullah | EchoMind Project\nabdullah@gmail.com",
        content_type="email", event_time=_d(5, 20, 0),
        participants=["abdullah@gmail.com", "abrar@gmail.com", "amaan@gmail.com"],
        metadata={"from": "abdullah@gmail.com", "to": ["abrar@gmail.com", "amaan@gmail.com"], "subject": "Semantic Search Query Examples"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_19",
        content="Subject: All Tests Passing\n\nHi team,\n\nRan all unit and integration tests. Everything passing. The full pipeline test ingests a sample message end to end and verifies the chunk appears in the DB with correct content type. Preprocessing tests check extraction and cleaning. Ready for the final run.\n\nAmaan\n\n--\nAmaan | EchoMind Project\namaan@gmail.com",
        content_type="email", event_time=_d(6, 10, 0),
        participants=["amaan@gmail.com", "abrar@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "amaan@gmail.com", "to": ["abrar@gmail.com", "abdullah@gmail.com"], "subject": "All Tests Passing"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_20",
        content="Subject: Presentation Slides Ready\n\nHi team,\n\nSlides are ready. Seven slides covering problem, solution, architecture, pipeline walkthrough, preprocessing demo, semantic search demo, and roadmap. Sharing the outline on WhatsApp.\n\nAbrar\n\n--\nAbrar Farooq\nabrar@gmail.com",
        content_type="email", event_time=_d(6, 14, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "abrar@gmail.com", "to": ["amaan@gmail.com", "abdullah@gmail.com"], "subject": "Presentation Slides Ready"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_21",
        content="Subject: Final Checklist Before Presentation\n\nDear team,\n\nFinal checklist: schema migrated on lab machine, seed script run, Ollama running, pgvector active, preprocessing complete, embeddings computed, demo queries tested. Let's arrive at 9:30 tomorrow.\n\nAbrar\n\n--\nAbrar Farooq\nabrar@gmail.com",
        content_type="email", event_time=_d(6, 22, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"from": "abrar@gmail.com", "to": ["amaan@gmail.com", "abdullah@gmail.com"], "subject": "Final Checklist Before Presentation"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_22",
        content="Subject: Re: Final Checklist Before Presentation\n\nAll done on my end. DB is up, preprocessing ran overnight, all chunks cleaned.\n\n– Abdullah\n\nOn Sat, Apr 25, 2026 at 10:00 PM Abrar <abrar@gmail.com> wrote:\n\n> Dear team,\n>\n> Final checklist: schema migrated on lab machine, seed script run,\n> Ollama running, pgvector active, preprocessing complete, embeddings\n> computed, demo queries tested. Let's arrive at 9:30 tomorrow.\n>\n> Abrar",
        content_type="email", event_time=_d(6, 22, 30),
        participants=["abdullah@gmail.com", "abrar@gmail.com"],
        metadata={"from": "abdullah@gmail.com", "to": ["abrar@gmail.com"], "subject": "Re: Final Checklist Before Presentation"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_23",
        content="Subject: Re: Final Checklist Before Presentation\n\nSame here. Whisper is done, embeddings stored. Good to go.\n\n– Amaan\n\nOn Sat, Apr 25, 2026 at 10:00 PM Abrar <abrar@gmail.com> wrote:\n\n> Dear team,\n>\n> Final checklist: schema migrated on lab machine, seed script run,\n> Ollama running, pgvector active, preprocessing complete, embeddings\n> computed, demo queries tested. Let's arrive at 9:30 tomorrow.\n>\n> Abrar",
        content_type="email", event_time=_d(6, 22, 45),
        participants=["amaan@gmail.com", "abrar@gmail.com"],
        metadata={"from": "amaan@gmail.com", "to": ["abrar@gmail.com"], "subject": "Re: Final Checklist Before Presentation"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_24",
        content="Subject: EchoMind Submission\n\nDear Ma'am,\n\nPlease find the EchoMind project repository link attached to this email. The README contains full setup instructions. We are ready for the presentation tomorrow at 10:00 AM.\n\nRegards,\nAbrar, Amaan, Abdullah\n\n--\nEchoMind Major Project\nBatch 2024-25 | Computer Science",
        content_type="email", event_time=_d(7, 9, 0),
        participants=["abrar@gmail.com", "maam@university.edu"],
        metadata={"from": "abrar@gmail.com", "to": ["maam@university.edu"], "subject": "EchoMind Submission"},
    ),
    NormalizedInput(
        source_type="gmail", external_id="gmail_25",
        content="Subject: Re: EchoMind Submission\n\nReceived. See you at 10:00 AM.\n\nRegards,\nMa'am\n\nOn Sun, Apr 26, 2026 at 9:00 AM Abrar <abrar@gmail.com> wrote:\n\n> Dear Ma'am,\n>\n> Please find the EchoMind project repository link attached. The README\n> contains full setup instructions. We are ready for the presentation\n> tomorrow at 10:00 AM.\n>\n> Regards,\n> Abrar, Amaan, Abdullah",
        content_type="email", event_time=_d(7, 9, 30),
        participants=["maam@university.edu", "abrar@gmail.com"],
        metadata={"from": "maam@university.edu", "to": ["abrar@gmail.com"], "subject": "Re: EchoMind Submission"},
    ),

    # ── CALENDAR (15) ─────────────────────────────────────────────────────────

    NormalizedInput(
        source_type="calendar", external_id="calendar_1",
        content="EchoMind Kickoff Meeting – Finalise architecture, divide tasks, set deadlines.",
        content_type="text", event_time=_d(1, 9, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"event_type": "meeting", "location": "Online", "duration_minutes": 60},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_2",
        content="Deadline: WhatsApp and Gmail connectors working end to end.",
        content_type="text", event_time=_d(2, 18, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com"],
        metadata={"event_type": "deadline"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_3",
        content="Deadline: Database schema finalised and pushed to repo.",
        content_type="text", event_time=_d(2, 18, 0),
        participants=["abdullah@gmail.com"],
        metadata={"event_type": "deadline"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_4",
        content="Mid-Project Review with Ma'am – Demo WhatsApp connector and architecture walkthrough. Bring printed architecture diagram.",
        content_type="text", event_time=_d(3, 11, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com", "maam@university.edu"],
        metadata={"event_type": "meeting", "location": "Ma'am's Office", "duration_minutes": 60},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_5",
        content="Deadline: Preprocessing pipeline complete and tested.",
        content_type="text", event_time=_d(3, 18, 0),
        participants=["amaan@gmail.com"],
        metadata={"event_type": "deadline"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_6",
        content="Team Sync – Day 4 post-meeting debrief. Review Ma'am's feedback, update action items.",
        content_type="text", event_time=_d(4, 14, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"event_type": "meeting", "location": "Online", "duration_minutes": 30},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_7",
        content="Deadline: Semantic layer embeddings stored and salience scoring complete.",
        content_type="text", event_time=_d(5, 18, 0),
        participants=["abdullah@gmail.com"],
        metadata={"event_type": "deadline"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_8",
        content="Day 5 Regroup – Check progress on all layers, prepare demo query list for Ma'am.",
        content_type="text", event_time=_d(5, 15, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"event_type": "meeting", "location": "Online", "duration_minutes": 45},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_9",
        content="Demo Rehearsal – Full end-to-end demo run. Test all ten demo queries. Time each section.",
        content_type="text", event_time=_d(6, 15, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"event_type": "meeting", "location": "Lab", "duration_minutes": 90},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_10",
        content="Overnight Preprocessing Run – Run preprocessing and semantic layer on all seed data. Do not shut down machine.",
        content_type="text", event_time=_d(6, 22, 0),
        participants=["abrar@gmail.com"],
        metadata={"event_type": "task"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_11",
        content="Final Submission Deadline – Submit project repository and documentation.",
        content_type="text", event_time=_d(7, 9, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"event_type": "deadline"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_12",
        content="EchoMind Presentation – 10:00 AM in Lab 3. Arrive by 9:30 to set up. Ma'am and evaluators attending.",
        content_type="text", event_time=_d(7, 10, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com", "maam@university.edu"],
        metadata={"event_type": "presentation", "location": "Lab 3", "duration_minutes": 60},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_13",
        content="Lab Machine Setup – Migrate schema, run seed script, start Ollama, verify pgvector.",
        content_type="text", event_time=_d(7, 9, 30),
        participants=["abrar@gmail.com", "abdullah@gmail.com"],
        metadata={"event_type": "task", "location": "Lab 3"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_14",
        content="Catch up with Hadi – Show him final demo, get last-minute feedback.",
        content_type="text", event_time=_d(6, 12, 0),
        participants=["abrar@gmail.com"],
        metadata={"event_type": "meeting", "location": "Canteen"},
    ),
    NormalizedInput(
        source_type="calendar", external_id="calendar_15",
        content="Post-Submission Debrief – Discuss what went well, what to improve, plan for open-source release.",
        content_type="text", event_time=_d(7, 14, 0),
        participants=["abrar@gmail.com", "amaan@gmail.com", "abdullah@gmail.com"],
        metadata={"event_type": "meeting", "location": "Canteen", "duration_minutes": 60},
    ),

    # ── MANUAL (20) ───────────────────────────────────────────────────────────

    NormalizedInput(
        source_type="manual", external_id="manual_1",
        content="Architecture is finalised. Three layers: ingestion, preprocessing, semantic. Each layer is independently testable. Starting WhatsApp connector tomorrow morning.",
        content_type="text", event_time=_d(1, 21, 0),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_3",
        content="WhatsApp connector working. Text, document, and audio message types all handled. Media bytes saved to disk, linked to memory chunk via FK. Ingestion pipeline passing end to end.",
        content_type="text", event_time=_d(2, 20, 0),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_5",
        content="Amaan's preprocessing notes are solid. The 2000 char truncation for LLM cleaning is a known limitation – acceptable for MVP. Full content still stored in DB.",
        content_type="document", event_time=_d(2, 21, 0),
        participants=["Abrar"],
        metadata={"note_type": "review"},
        media=[_docx("notes_6.docx", _d(2, 21, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_6",
        content="Meeting with Ma'am went well. She liked the architecture. Main ask: make salience scores visible in demo. Also wants a video backup. Action: Abdullah adds score to search result output.",
        content_type="text", event_time=_d(3, 13, 0),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_7",
        content="TODO: update README with full setup instructions before submission. Sections needed: prerequisites, installation, running the seed script, running the pipeline.",
        content_type="text", event_time=_d(3, 14, 0),
        participants=["Abrar"],
        metadata={"note_type": "todo"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_8",
        content="Hadi's DOCX feedback is useful. Cross-source search is a killer feature – definitely demo it. Web UI post-submission priority 1.",
        content_type="document", event_time=_d(4, 17, 0),
        participants=["Abrar"],
        metadata={"note_type": "review"},
        media=[_docx("notes_3.docx", _d(4, 17, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_9",
        content="Semantic layer notes from Abdullah look good. HNSW index is the right call for nearest-neighbour search. No partitioning for MVP is fine.",
        content_type="document", event_time=_d(4, 18, 0),
        participants=["Abrar"],
        metadata={"note_type": "review"},
        media=[_docx("notes_5.docx", _d(4, 18, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_10",
        content="Went through the risk register. Biggest risk is Ollama latency during live demo. Will pre-run preprocessing the night before. Should be fine.",
        content_type="text", event_time=_d(5, 10, 0),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_11",
        content="Sent Ma'am the Day 5 update. She specifically asked for salience scores to be visible. Abdullah is on it. Demo queries list is finalised.",
        content_type="text", event_time=_d(5, 19, 0),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_12",
        content="Project timeline doc for reference. We're on track.",
        content_type="document", event_time=_d(5, 20, 0),
        participants=["Abrar"],
        metadata={"note_type": "reference"},
        media=[_docx("notes_8.docx", _d(5, 20, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_13",
        content="Demo rehearsal done. All ten queries returning relevant results. Salience scores visible. Average query time is under 2 seconds. Ready.",
        content_type="text", event_time=_d(6, 17, 0),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_14",
        content="Semantic search demo query examples for presentation. Keep this open during the demo.",
        content_type="document", event_time=_d(6, 18, 0),
        participants=["Abrar"],
        metadata={"note_type": "reference"},
        media=[_docx("notes_10.docx", _d(6, 18, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_15",
        content="Abrar's connector notes saved for future reference.",
        content_type="document", event_time=_d(6, 19, 0),
        participants=["Abrar"],
        metadata={"note_type": "reference"},
        media=[_docx("notes_7.docx", _d(6, 19, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_16",
        content="Preprocessing pipeline is the slowest part of the system. For future work: parallelise chunk processing, add streaming support for large files.",
        content_type="text", event_time=_d(6, 20, 0),
        participants=["Abrar"],
        metadata={"note_type": "future_work"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_17",
        content="What we learned doc. Good to have this written up. Will use it in the final presentation conclusion slide.",
        content_type="document", event_time=_d(6, 21, 0),
        participants=["Abrar"],
        metadata={"note_type": "reflection"},
        media=[_docx("notes_11.docx", _d(6, 21, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_18",
        content="Submission done. Repository link sent to Ma'am. Presentation tomorrow at 10. Everything is ready.",
        content_type="text", event_time=_d(7, 9, 15),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_19",
        content="Post-submission plan document. Open-source after cleanup is the goal.",
        content_type="document", event_time=_d(7, 14, 30),
        participants=["Abrar"],
        metadata={"note_type": "future_work"},
        media=[_docx("notes_12.docx", _d(7, 14, 30))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_20",
        content="EchoMind demo went well. Ma'am was impressed by the WhatsApp integration and the semantic search. Salience scores were visible and she noticed. Good outcome.",
        content_type="text", event_time=_d(7, 11, 30),
        participants=["Abrar"],
        metadata={"note_type": "daily_log"},
    ),

    # ── EXTRA: cover remaining manifest files ─────────────────────────────────

    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_41",
        content="Testing and validation plan document – go through this before Day 6.",
        content_type="document", event_time=_d(5, 12, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Amaan", "caption": "Testing and validation plan document – go through this before Day 6."},
        media=[_pdf("report_5.pdf", _d(5, 12, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_42",
        content="Presentation outline is ready. Seven slides, check it out.",
        content_type="document", event_time=_d(6, 15, 0),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abrar", "caption": "Presentation outline is ready. Seven slides, check it out."},
        media=[_pdf("report_6.pdf", _d(6, 15, 0))],
    ),
    NormalizedInput(
        source_type="whatsapp", external_id="whatsapp_43",
        content="Risk register attached. Read before the presentation.",
        content_type="document", event_time=_d(5, 9, 30),
        participants=WA_ALL, metadata={"chat": "group", "sender": "Abdullah", "caption": "Risk register attached. Read before the presentation."},
        media=[_pdf("report_7.pdf", _d(5, 9, 30))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_21",
        content="Semantic layer design notes – how embeddings and salience scoring work.",
        content_type="document", event_time=_d(4, 19, 0),
        participants=["Abrar"],
        metadata={"note_type": "reference"},
        media=[_pdf("report_11.pdf", _d(4, 19, 0))],
    ),
    NormalizedInput(
        source_type="manual", external_id="manual_22",
        content="Feature checklist – tracking what's done and what's left.",
        content_type="document", event_time=_d(3, 20, 0),
        participants=["Abrar"],
        metadata={"note_type": "reference"},
        media=[_docx("notes_2.docx", _d(3, 20, 0))],
    ),
]

if __name__ == "__main__":
    print(f"Ingesting {len(inputs)} items...")
    process(inputs)
    print(f"Done. {len(inputs)} items ingested.")
