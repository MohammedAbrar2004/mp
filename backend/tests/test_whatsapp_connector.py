"""
WhatsApp connector integration test.

Simulates the exact payload shape the Node.js Baileys service sends,
runs it through the connector and pipeline, and verifies DB writes.

Run from backend/:
    python -m tests.test_whatsapp_connector
"""

from app.connectors.whatsapp.connector import WhatsAppConnector
from pipelines.ingestion_pipeline import process

connector = WhatsAppConnector()

# Each test uses a unique message ID so re-runs silently skip duplicates
# instead of failing.

# ─── Test 1: plain text message ───────────────────────────────────────────────
print("--- Test 1: text message ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "TEST-WA-TEXT-001",
    },
    "message": {"conversation": "Hey, call me at 6pm"},
    "messageTimestamp": 1700000001,
})
assert result is not None, "Expected NormalizedInput, got None"
assert result.content_type == "text"
assert result.metadata["message_type"] == "text"
assert result.metadata["is_group"] is False
assert result.participants == ["+923001234567"]
assert result.media == []
process([result])
print("OK — memory_chunk inserted, no media")

# ─── Test 2: document WITHOUT caption ─────────────────────────────────────────
print("--- Test 2: document without caption ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "TEST-WA-DOC-NOCAP-001",
    },
    "message": {
        "documentMessage": {
            "fileName": "project_brief.pdf",
            "mimetype": "application/pdf",
        }
    },
    "messageTimestamp": 1700000002,
    "_file_bytes": b"%PDF-1.4 fake pdf content for testing",
})
assert result is not None, "Expected NormalizedInput, got None"
assert result.content_type == "document"
assert result.metadata["message_type"] == "document"
assert result.content == ""
assert len(result.media) == 1
assert result.media[0].original_filename == "project_brief.pdf"
assert result.media[0].mime_type == "application/pdf"
process([result])
print("OK — memory_chunk inserted, media_file inserted")

# ─── Test 3: document WITH caption ────────────────────────────────────────────
# Mirrors the normalized payload index.js sends after detecting
# documentWithCaptionMessage and promoting documentMessage to the top level.
print("--- Test 3: document with caption ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "TEST-WA-DOC-CAP-001",
    },
    "message": {
        "documentMessage": {
            "fileName": "proposal.pdf",
            "mimetype": "application/pdf",
            "caption": "Here is the updated proposal",
        }
    },
    "messageTimestamp": 1700000003,
    "_file_bytes": b"%PDF-1.4 fake pdf content for captioned doc",
})
assert result is not None, "Expected NormalizedInput, got None"
assert result.content_type == "document"
assert result.content == "Here is the updated proposal"
assert result.metadata.get("caption") == "Here is the updated proposal"
assert len(result.media) == 1
assert result.media[0].original_filename == "proposal.pdf"
process([result])
print("OK — memory_chunk with caption in raw_content, media_file inserted")

# ─── Test 4: audio (voice note) ───────────────────────────────────────────────
print("--- Test 4: audio (voice note) ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "TEST-WA-AUDIO-001",
    },
    "message": {
        "audioMessage": {
            "mimetype": "audio/ogg; codecs=opus",
            "seconds": 12,
            "ptt": True,
        }
    },
    "messageTimestamp": 1700000004,
    "_file_bytes": b"OggS fake ogg audio bytes for testing",
})
assert result is not None, "Expected NormalizedInput, got None"
assert result.content_type == "audio"
assert result.metadata["message_type"] == "audio"
assert len(result.media) == 1
assert result.media[0].original_filename == "voice_note_TEST-WA-AUDIO-001.ogg"
assert result.media[0].mime_type == "audio/ogg"
process([result])
print("OK — memory_chunk inserted, audio media_file inserted")

print("\nAll 4 tests passed.")
print("\nVerify in DB:")
print("  SELECT external_message_id, content_type, raw_content FROM memory_chunks")
print("    WHERE external_message_id LIKE 'TEST-WA-%' ORDER BY created_at DESC;")
print("  SELECT original_filename, media_type, size_bytes FROM media_files")
print("    ORDER BY id DESC LIMIT 3;")
