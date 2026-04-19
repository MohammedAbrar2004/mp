EchoMind — TODO (Final Consolidated)
HIGH PRIORITY (Before scaling further)
Metadata Standardization
Define strict schema across all connectors
Include:
sender
chat_id / thread_id
caption
subject (email)
direction (email)
event_title (calendar)
Ensure no random keys are used
Participants Model
Decide meaning:
sender only (reject)
all involved users (accept)
Keep raw for now
Future: contacts table (phone → name mapping)
Include source-specific identifiers:
phone (WhatsApp)
email (Gmail / Calendar)
Source to Source_ID Mapping
Remove hardcoded mappings in pipeline
Fetch dynamically from data_sources table
Enforce is_active
Skip ingestion if connector is disabled
Update last_synced
After each ingestion update timestamp
Required for incremental sync
Email Fetch Optimization
Replace fixed limit fetch with last_synced-based queries
Avoid redundant fetching
Content Cleaning Layer
Add DB fields:
content
is_cleaned
Cleaning must happen in pipeline/service
Do not implement inside connectors
LLM-based cleaning planned
Calendar Multi-Calendar Handling
Ensure events are fetched from all calendars
Store calendar_id in metadata
Timezone Handling Standardization
Store all timestamps in UTC
Convert to local only at display layer
Ensure consistency across all connectors
Deduplication Contract
Use UNIQUE (source_id, external_id)
Ensure all connectors follow this pattern
Do not implement dedup logic in connectors
Connector Output Validation
Ensure every connector returns valid NormalizedInput
Validate:
external_id is not null
event_time is correct
structure is consistent
MEDIUM PRIORITY (After connectors are built)
Media Metadata Enrichment
Add:
caption
sender
timestamp
Improve linkage between media_files and memory_chunks
Media Naming Improvements
Voice:
voice_note_<external_id>.ogg
Documents:
preserve original filename
Event Time Consistency
Ensure event_time reflects actual occurrence time
Not ingestion time
Email Improvements
Ensure:
participants are clean
subject is consistent
direction is accurate
Calendar Schema
Define structured metadata:
title
start_time
end_time
participants
calendar_id
is_all_day
Participants Normalization
Normalize values such as:
"GitHub support@github.com
" → support@github.com

Avoid storing noisy strings
Media Processing Service
Build centralized service for:
audio transcription
document parsing
Output cleaned content for pipeline
Drive-Based Ingestion Strategy
Implement Google Drive connector
Ingest:
transcripts
call recordings
Treat all as documents
Reuse media processing service
Multi-day Event Handling
Handle events spanning multiple days
Decide representation strategy later
Noise Classification
Tag entries such as:
holidays
observances
newsletters
Do not filter yet, only classify
LOW PRIORITY (Refinement)
Background Scheduler
Poll connectors periodically
Enable passive ingestion
Logging Standardization
Unify logs across connectors, pipeline, and DB
Error Handling
Add retry logic
Handle partial failures
Cleanup
Remove test and dummy data
DB Optimization
Add indexes
Improve query performance
Data Source Config Layer
Store connector configurations centrally
Remove dependency on env and hardcoding
Incremental Sync Strategy
Use last_synced across all connectors
Avoid full re-fetch cycles
Schema Migration Plan
Plan for DB schema evolution
Handle future changes safely
FUTURE (Do not implement now)
Semantic Layer
Entity extraction
Event detection
Relationship identification
Knowledge Graph
Entities table
Events table
Entity-event relationships
Retrieval Layer
Hybrid search (SQL + vector)
Time-aware ranking
UI Layer
DESIGN RULES

Connectors must remain pure
No DB logic in connectors
Pipeline handles orchestration
Services handle processing logic
Raw data must always be preserved
Cleaning is separate from ingestion
Ingestion is separate from understanding

CURRENT STATUS

WhatsApp connector complete
Gmail connector complete
Calendar connector complete
Media handling stable
Pipeline working