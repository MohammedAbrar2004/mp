🧠 EchoMind — TODO (Final Consolidated)
🔴 HIGH PRIORITY (Before scaling further)
1. Metadata Standardization
Define strict schema across all connectors
Include:
sender
chat_id / thread_id
caption
subject (email)
direction (email)
event_title (calendar)
❗ No random keys allowed
2. Participants Model (IMPORTANT)
Decide meaning:
sender only ❌
all involved users ✅
Keep raw for now
🔜 Future: contacts table (phone → name mapping)
3. Source → Source_ID Mapping (REMOVE HARDCODE)
Replace:
# TODO
Fetch from data_sources table dynamically
4. Enforce is_active
Skip ingestion if connector disabled
5. Update last_synced
After ingestion → update timestamp
Needed later for Gmail query filtering
6. 🆕 Email Fetch Optimization (IMPORTANT)
Replace:
limit = 50
With:
Gmail query using last_synced
Prevent unnecessary fetches
7. 🆕 Content Cleaning Layer (CRITICAL DESIGN)
Add DB fields:
content
is_cleaned
Cleaning must happen in pipeline/service
❌ NOT in connectors
LLM-based cleaning (later)
🟡 MEDIUM PRIORITY (After all connectors)
8. Media Metadata Enrichment
Add:
caption
sender
timestamp
Better linkage with memory_chunks
9. Media Naming Improvements
Voice:
voice_note_<external_id>.ogg
Docs:
keep original filename ✔
10. Event Time Consistency
event_time = actual event time

NOT ingestion time

11. Email Improvements
Already partially done ✔
Still ensure:
clean participants
subject consistency
direction correctness
12. Calendar Schema
Define:
title
start_time
end_time
participants
Store structured metadata
13. 🆕 Participants Normalization
Extract clean values:
"GitHub <support@github.com>" → support@github.com
Avoid storing noisy strings
🟢 LOW PRIORITY (Refinement)
14. Background Scheduler
Poll connectors
Needed for real automation
15. Logging Standardization
Unified logs across:
connectors
pipeline
DB
16. Error Handling
Retry logic
Partial failures
17. Cleanup
Remove:
dummy users
test data (later)
18. DB Optimization
Indexes
Performance tuning
🔵 FUTURE (Do NOT touch now)
19. Semantic Layer
Entity extraction
Event detection
20. Knowledge Graph
entities
events
relationships
21. Retrieval Layer
hybrid search
time-aware ranking
22. UI Layer
⚠️ DESIGN RULES (LOCK THESE)
Connectors = PURE
No DB logic in connectors
Pipeline = orchestration
Services = logic
Raw data must ALWAYS be preserved
Cleaning ≠ ingestion
Ingestion ≠ understanding