# 🧠 EchoMind — TODO (Post-Ingestion + System Refinement)

---

## 🔴 HIGH PRIORITY (Soon — before scaling connectors)

### 1. Metadata Standardization

* Define consistent metadata schema across all connectors
* Include:

  * sender
  * chat_id / thread_id
  * caption
  * subject (for email)
  * event_title (for calendar)
* Ensure:

  * no random keys
  * consistent naming

---

### 2. Participants Model (IMPORTANT DESIGN DECISION)

* Decide:

  * What does `participants` represent?

    * sender only?
    * all involved users?
* Introduce **contacts table (future)**:

  * phone_number
  * display_name
* Keep ingestion raw for now, enrich later

---

### 3. Source → Source_ID Mapping (Remove Hardcoding)

* Replace hardcoded mapping in pipeline:

```python
# TODO: replace with DB lookup
```

* Fetch from `data_sources` table dynamically

---

### 4. Enforce `is_active` in ingestion

* Before processing:

  * check if connector is enabled
* Skip ingestion if disabled

---

### 5. Update `last_synced`

* After each successful ingestion:

  * update `data_sources.last_synced`

---

## 🟡 MEDIUM PRIORITY (After all connectors are built)

### 6. Media Metadata Enrichment

* Add:

  * caption (already started)
  * sender
  * timestamp
* Link media ↔ message more clearly

---

### 7. Media Naming Improvements

* Voice notes:

  * use `voice_note_<external_id>.ogg`
* Documents:

  * preserve original filename (already good)

---

### 8. Event Time Consistency

* Ensure all connectors use:

```text
event_time = actual occurrence time
```

NOT ingestion time

---

### 9. Email Improvements

* Track:

  * sent emails
  * received emails
* Store:

  * subject
  * thread_id
  * participants

---

### 10. Calendar Data Format

* Define structure:

  * title
  * start_time
  * end_time
  * participants
* Store as structured metadata

---

## 🟢 LOW PRIORITY (Refinement / Optimization)

### 11. Background Scheduler

* Build after connectors are stable
* Handle:

  * Gmail polling
  * Calendar sync
  * GMeet fetch

---

### 12. Logging Improvements

* Standardize logs across:

  * connectors
  * pipeline
  * DB

---

### 13. Error Handling Improvements

* Retry logic (later)
* Partial failure handling

---

### 14. Remove Test / Dummy Data

* Clean:

  * users table (if needed)
  * data_sources (optional reset)

---

### 15. DB Optimization

* Indexes (later)
* Query performance (later)

---

## 🔵 FUTURE (DO NOT TOUCH NOW)

### 16. Semantic Layer (Layer 3)

* Entity extraction
* Event detection
* Relationship building

---

### 17. Knowledge Graph (Layer 4)

* entities table
* events table
* links

---

### 18. Retrieval Layer

* hybrid search:

  * SQL + vector
  * time-aware ranking

---

### 19. UI Layer

* only after backend is stable

---

## ⚠️ DESIGN REMINDERS

* Connectors MUST stay pure
* No DB logic in connectors
* Media processing is separate service
* Ingestion ≠ understanding

---

## ✅ CURRENT STATUS

* WhatsApp ingestion → COMPLETE ✅
* Media handling → STABLE ✅
* Pipeline → WORKING ✅

---

## 🚀 NEXT

→ Gmail Connector
