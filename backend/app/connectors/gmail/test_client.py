"""
Gmail client smoke test.

Run from backend/:
    python -m app.connectors.gmail.test_client
"""

from app.connectors.gmail.client import fetch_recent_emails

emails = fetch_recent_emails(5)

for e in emails:
    print(f"source_type: {e.source_type}")
    print(f"external_id: {e.external_id}")
    print(f"content:     {e.content[:100]!r}")
    print(f"metadata:    {e.metadata}")
    print(f"media:       {len(e.media)} attachment(s)")
    print()

print(f"Fetched {len(emails)} email(s).")
