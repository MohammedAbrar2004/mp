from app.connectors.calendar.client import fetch_upcoming_events
from pipelines.ingestion_pipeline import process


def run():
    events = fetch_upcoming_events(limit=50)

    if not events:
        print("No events fetched.")
        return

    print(f"Fetched {len(events)} events. Sending to pipeline...")

    process(events)

    print("Calendar ingestion completed.")


if __name__ == "__main__":
    run()
