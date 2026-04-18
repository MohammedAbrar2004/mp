"""
WhatsApp connector integration test.

Run from backend/:
    python -m app.connectors.whatsapp.test_connector
    # NOTE:
# This test bypasses the connector and simulates post-normalized input.
# Real connector parsing is validated via live WhatsApp ingestion.
"""

from app.connectors.whatsapp.connector import WhatsAppConnector
from pipelines.ingestion_pipeline import process

connector = WhatsAppConnector()

TIMESTAMP = 1700000000  # fixed Unix ts — avoids duplicate collisions across test runs

# --- Test 1: plain text message ---
print("--- Test 1: text message ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "WA-TEXT-001",
    },
    "message": {"conversation": "Hey, call me at 6pm"},
    "messageTimestamp": TIMESTAMP,
})
assert result is not None, "Expected NormalizedInput, got None"
assert result.metadata["message_type"] == "text"
assert result.metadata["is_group"] is False
assert result.participants == ["+923001234567"]
process([result])
print("OK")

# --- Test 2: document (PDF) ---
print("--- Test 2: document (PDF) ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "WA-DOC-001",
    },
    "message": {
        "documentMessage": {
            "fileName": "project_brief.pdf",
            "mimetype": "application/pdf",
        }
    },
    "messageTimestamp": TIMESTAMP,
    "_file_bytes": b"%PDF fake pdf content",
})
assert result is not None
assert result.metadata["message_type"] == "document"
assert len(result.media) == 1
assert result.media[0].original_filename == "project_brief.pdf"
process([result])
print("OK")

# --- Test 3: audio (voice note) ---
print("--- Test 3: audio (voice note) ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "WA-AUDIO-001",
    },
    "message": {
        "audioMessage": {
            "mimetype": "audio/ogg; codecs=opus",
            "seconds": 12,
            "ptt": True,
        }
    },
    "messageTimestamp": TIMESTAMP,
    "_file_bytes": b"OGG fake audio bytes",
})
assert result is not None
assert result.metadata["message_type"] == "audio"
assert len(result.media) == 1
process([result])
print("OK")

# --- Test 4: group message ---
print("--- Test 4: group message ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "120363000000000001@g.us",
        "fromMe": False,
        "id": "WA-GROUP-001",
    },
    "participant": "923009876543@s.whatsapp.net",
    "message": {"conversation": "Team lunch at 1pm?"},
    "messageTimestamp": TIMESTAMP,
})
assert result is not None
assert result.metadata["is_group"] is True
assert result.participants == ["+923009876543"]
process([result])
print("OK")

# --- Test 5: extended text message ---
print("--- Test 5: extendedTextMessage ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "WA-EXT-001",
    },
    "message": {
        "extendedTextMessage": {
            "text": "Check this link",
            "matchedText": "https://example.com",
        }
    },
    "messageTimestamp": TIMESTAMP,
})
assert result is not None
assert result.content == "Check this link"
process([result])
print("OK")

# --- Test 6: unknown message type (sticker, reaction, etc.) ---
print("--- Test 6: unknown type → skipped ---")
result = connector.handle_message({
    "key": {
        "remoteJid": "923001234567@s.whatsapp.net",
        "fromMe": False,
        "id": "WA-UNKNOWN-001",
    },
    "message": {"stickerMessage": {"url": "..."}},
    "messageTimestamp": TIMESTAMP,
})
assert result is None, "Expected None for unsupported message type"
print("OK (correctly returned None)")

print("\nAll tests passed.")
