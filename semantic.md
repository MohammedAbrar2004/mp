🧠 EchoMind — Final Flow (Locked)

🔹 1. Ingestion
Connector → NormalizedInput → ingestion_pipeline → DB write

Data stored:

raw_content
metadata
participants
media (saved to media_files) also saved locally on disc

👉 No LLM, no meaning, no salience


🔹 2. Preprocessing (Post-Ingestion)

Happens in stages:

🧩 Media Processing
media_files → extracted_content filled
PDF → text
audio → transcription

🧩 Cleaning
raw_content → content (cleaned)

🧩 Salience (Initial)
initial_salience → heuristic

Used to decide:
Should this go to semantic layer?

🧩 Embeddings
content → embedding

🔹 3. memory_chunks Completion
memory_chunks is filled in stages (not all at once)

Final usable state:

raw_content
content (cleaned)
extracted_content (via media)
initial_salience
embedding
metadata
flags


🔹 4. Semantic Layer Input

Each memory_chunk is converted into a runtime object:
{
  "memory_chunk_id": "...",
  "content": "...",
  "timestamp": "...",
  "metadata": {...},
  "participants": [...],
  "media": [
    {
      "type": "...",
      "extracted_content": "..."
    }
  ]
}

👉 Media is fetched using:

SELECT * FROM media_files WHERE memory_chunk_id = ?

👉 Final input =
content + all extracted_content



🔹 5. Semantic Layer (LLM)

LLM processes the input and outputs:

entities
events
relationships
refined_salience


🔹 6. Salience Logic
initial_salience → decides WHAT to send
refined_salience → decides WHAT to keep


🔹 7. Knowledge Structuring Layer

LLM output → validated → written to DB:

entities table (upsert)
events table (create/dedup)
entity_event_links
event_memory_links


🔹 8. Finalization
memory_chunk.is_processed = true
refined_salience stored


🧠 Key Principles

✔ Staged Data Filling
memory_chunks is NOT filled in one go
✔ Separation of Concerns
Ingestion = storage
Preprocessing = cleaning
Semantic = understanding
Graph = structure
✔ Salience Controls Everything
Without salience → noise
With salience → meaningful knowledge
✔ Media is First-Class Input
Attachments are merged into semantic input
✔ LLM Never Touches DB Directly
LLM → structured output → validated → DB write
🧠 One-Line Mental Model
Store → Clean → Filter → Understand → Structure