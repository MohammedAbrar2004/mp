"""
Google Calendar client smoke test.

Run from backend/:
    python -m app.connectors.calendar.test_client
"""

from app.connectors.calendar.client import fetch_upcoming_events

events = fetch_upcoming_events(10)

for e in events:
    print(e.source_type)
    print(e.external_id)
    print(e.content)
    print(e.event_time.astimezone())
    print(e.participants)
    print(e.metadata)
    print()

print(f"Fetched {len(events)} event(s).")
