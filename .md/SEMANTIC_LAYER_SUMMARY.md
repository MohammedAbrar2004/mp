# EchoMind Semantic Layer Implementation Summary

## Files Created

All files are in `backend/app/semantic/`:

### 1. `schemas.py`
- **Purpose**: Pydantic v2 data contracts for LLM output
- **Classes**:
  - `Entity`: name + type (person|project|organization|tool|technology|topic|task)
  - `Event`: title + summary + event_type + timestamp
  - `Relationship`: entity + role
  - `SemanticOutput`: entities + event + relationships + refined_salience

### 2. `extractor.py`
- **Purpose**: Pure LLM extraction, no DB access
- **Key Functions**:
  - `build_prompt()`: Constructs Mistral `[INST]...[/INST]` prompt with strict JSON requirements
  - `_call_ollama()`: HTTP POST to Ollama, 3-retry loop, `temperature=0.1`
  - `_sanitize_output()`: Strips `<think>` blocks and prompt leakage
  - `extract()`: Public entry point
- **Config**:
  - Model: `mistral:7b-instruct-q4_0`
  - URL: `http://localhost:11434/api/chat`
  - Max input: 3000 chars
  - Timeout: 120s

### 3. `db_writer.py`
- **Purpose**: All database writes, no LLM calls
- **Functions**:
  - `write_entities()`: Upserts entities with conflict resolution on `(normalized_name, entity_type, user_id)`
  - `write_event()`: Inserts event, returns event_id
  - `write_relationships()`: Links entities to event via `entity_event_links`
  - `write_event_memory_link()`: Links event to source chunk
  - `update_refined_salience()`: Writes LLM-computed salience back to memory_chunks

### 4. `processor.py`
- **Purpose**: Orchestrates semantic extraction pipeline
- **Key Functions**:
  - `_fetch_eligible_chunks()`: WHERE `initial_salience >= 0.4 AND is_processed = false`
  - `_build_semantic_input()`: Combines `content` + media + participants
  - `_validate_and_normalize_output()`: JSON parse, schema validation, deduplication, fallback event_type
  - `_mark_processed()`: Sets `is_processed = true`
  - `run_semantic()`: Main entry point — processes one chunk at a time
- **Salience Routing**:
  - `>= 0.7`: write event + entities + relationships + event_memory_link
  - `>= 0.4`: write entities only
  - `< 0.4`: skip (mark processed anyway)

### 5. `run_semantic.py`
- **Purpose**: CLI entry point
- **Usage**: `python -m app.semantic.run_semantic`

### 6. `__init__.py`
- Empty module marker

---

## Architecture Compliance

### ✅ Layer Separation
- **extractor.py**: Zero DB imports, pure function
- **db_writer.py**: Zero LLM imports, all DB writes here
- **processor.py**: Orchestration only, no extraction logic, no write logic

### ✅ No Meaning Invention
- LLM prompt explicitly forbids hallucination and inference
- `_validate_and_normalize_output()` enforces schema
- Unknown values fall back to safe defaults (`event_type → "other"`)

### ✅ One Chunk at a Time
- `run_semantic()` processes rows sequentially
- Per-chunk failure does not crash pipeline
- Always mark processed even on failure (avoid infinite loops)

### ✅ DB Pattern Match
- Follows preprocessing layer pattern: `_fetch_*()` → service → `_update_*()`
- Manual `conn.commit()` / `conn.rollback()` per operation
- Uses `psycopg2` raw SQL (no ORM)

---

## Testing

### Dry Run (no DB writes)
```bash
cd backend/app/semantic
python -m test_semantic_dry_run
```
- Fetches eligible chunks
- Calls LLM extraction
- Prints JSON output (no DB writes)

### Live Run (with DB writes)
```bash
python -m run_semantic
```
- Processes eligible chunks
- Writes entities, events, relationships
- Logs per-chunk results

### Verify DB
```sql
SELECT * FROM entities LIMIT 10;
SELECT * FROM events LIMIT 10;
SELECT * FROM entity_event_links LIMIT 10;
SELECT * FROM event_memory_links LIMIT 10;
SELECT id, is_processed, initial_salience, refined_salience 
FROM memory_chunks WHERE is_processed = true LIMIT 10;
```

---

## Event Type Mapping

DB allows: `decision|meeting|task|discussion|milestone|other`

LLM is instructed to use only these values. Fallback: `other`

---

## Dependencies

- `psycopg2`: DB access (already in project)
- `requests`: HTTP to Ollama (already in project)
- `pydantic`: v2 (already in project)
- Standard library: `json`, `logging`, `time`, `datetime`, `re`

---

## Next Steps

1. ✅ Run dry run to test LLM extraction
2. ✅ Run live semantic layer to populate DB
3. ✅ Verify data in entities/events/relationships tables
4. ❌ (Future) Wire into preprocessing_pipeline.py orchestrator
5. ❌ (Future) Add embedding layer (Layer 4)

