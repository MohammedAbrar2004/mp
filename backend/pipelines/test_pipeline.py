from pipelines.ingestion_pipeline import process
from models.normalized_input import NormalizedInput, PendingMedia
from datetime import datetime, timezone

now = datetime.now(timezone.utc)

# Test 1: text message, no media
print("--- Test 1: text message ---")
process([NormalizedInput(
    source_type="whatsapp",
    external_id="test-unique-001",
    content="Call me at 5pm",
    content_type="text",
    event_time=now,
    participants=["+92300000000"],
    metadata={},
)])
print("OK")

# Test 2: with PDF media
print("--- Test 2: with media ---")
process([NormalizedInput(
    source_type="gmail",
    external_id="gmail-unique-002",
    content="See attached",
    content_type="email",
    event_time=now,
    participants=["user@example.com"],
    metadata={},
    media=[PendingMedia(
        raw_bytes=b"%PDF fake",
        original_filename="doc.pdf",
        mime_type="application/pdf",
        captured_at=now,
    )],
)])
print("OK")

# Test 3: duplicate — same external_id (should not raise)
print("--- Test 3: duplicate ---")
process([NormalizedInput(
    source_type="whatsapp",
    external_id="test-unique-001",
    content="Call me at 5pm",
    content_type="text",
    event_time=now,
    participants=["+92300000000"],
    metadata={},
)])
print("OK (silently skipped)")

# Test 4: unknown source_type (should print warning, not raise)
print("--- Test 4: unknown source_type ---")
process([NormalizedInput(
    source_type="unknown",
    external_id="x",
    content="hi",
    content_type="text",
    event_time=now,
    participants=[],
    metadata={},
)])
print("OK")
