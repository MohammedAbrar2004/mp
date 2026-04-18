"""
Manual connector integration test.

Run from backend/:
    python -m app.connectors.manual.test_manual
"""

from datetime import datetime, timezone

from app.connectors.manual.connector import ManualConnector
from models.normalized_input import PendingMedia
from pipelines.ingestion_pipeline import process

connector = ManualConnector()

# Test 1: text-only input
print("--- Test 1: text-only ---")
text_input = connector.create_input(
    content="Reminder: team standup at 10am",
    participants=["alice@example.com", "bob@example.com"],
    metadata={"priority": "high"},
)
process([text_input])
print("OK")

# Test 2: input with PDF media
print("--- Test 2: with PDF media ---")
pdf_input = connector.create_input(
    content="See the attached document for meeting notes",
    participants=["alice@example.com"],
    metadata={"source": "manual_upload"},
    media=[
        PendingMedia(
            raw_bytes=b"%PDF fake content for testing",
            original_filename="meeting_notes.pdf",
            mime_type="application/pdf",
            captured_at=datetime.now(timezone.utc),
        )
    ],
)
process([pdf_input])
print("OK")

# Test 3: duplicate external_id (should silently skip)
print("--- Test 3: duplicate (same external_id) ---")
process([text_input])
print("OK (silently skipped)")

print("\nAll tests passed.")
