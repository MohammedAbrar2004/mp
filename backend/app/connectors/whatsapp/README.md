# WhatsApp Connector

Receives raw Baileys message payloads from the Node.js bridge, converts them
to `NormalizedInput` objects, and feeds them into the ingestion pipeline.

---

## Flow

```
WhatsApp → Node.js (Baileys) → FastAPI /whatsapp/webhook → WhatsAppConnector → Pipeline → DB
```

1. **Node.js** (`api/whatsapp/index.js`) maintains the Baileys connection, normalizes
   message formats, downloads media, and POSTs each message to the Python receiver.
2. **FastAPI receiver** (`app/api/whatsapp_receiver.py`) decodes the base64 media
   bytes and injects them as `_file_bytes` before handing off to the connector.
3. **Connector** (`connector.py`) parses the dict into a `NormalizedInput`.
4. **Pipeline** (`pipelines/ingestion_pipeline.py`) saves media to disk and writes
   `memory_chunks` + `media_files` rows.

---

## Supported Message Types

| WhatsApp type | content_type | Notes |
|---|---|---|
| `conversation` | `text` | Plain text message |
| `extendedTextMessage` | `text` | Link preview / long text |
| `documentMessage` | `document` | File without caption, or normalized captioned file |
| `documentWithCaptionMessage` | `document` | Handled at Node layer; arrives as `documentMessage` |
| `audioMessage` | `audio` | Voice notes |

---

## Caption Handling

Caption normalization happens entirely in the **Node layer** (`index.js`).

When WhatsApp delivers a document with a caption, Baileys wraps it as
`documentWithCaptionMessage`. The Node service detects this, promotes
`documentMessage` to the top level, and inlines the caption — so the Python
connector always sees a flat `{ documentMessage: { ..., caption: "..." } }`.

The connector never needs to know which Baileys wire format the message
originally used.

---

## Design Constraints

- **Connector is pure** — no DB writes, no file I/O, no HTTP calls.
- **Media is handled by `MediaService`** — the connector only populates
  `PendingMedia` objects; saving to disk is the pipeline's responsibility.
- **Each connector must remain independently runnable and testable.**
  Building new connectors must NOT break existing ones.

---

## How to Run

```bash
# Terminal 1 — Python backend (run from backend/)
uvicorn app.api.whatsapp_receiver:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Node bridge
cd api/whatsapp
npm start
```

Or use the run script (from `backend/`):

```bash
python run_whatsapp.py
```

---

## How to Test

```bash
# From backend/
python -m tests.test_whatsapp_connector
```

Tests simulate the exact payload shape the Node service sends and run each
message through the full connector → pipeline → DB path. Four cases are
covered: text, document without caption, document with caption, audio.

---

## Verify in DB

```sql
SELECT external_message_id, content_type, raw_content
  FROM memory_chunks ORDER BY created_at DESC LIMIT 10;

SELECT original_filename, media_type, local_path, size_bytes
  FROM media_files ORDER BY id DESC LIMIT 5;
```
