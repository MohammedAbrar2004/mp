import logging

from app.connectors.calendar.client import fetch_upcoming_events
from pipelines.ingestion_pipeline import process

logger = logging.getLogger("echomind.ingestion.calendar")


def run():
    logger.info("Fetching calendar events (±30 days, limit=50)...")
    events = fetch_upcoming_events(limit=50)
    logger.info("Fetched %d events", len(events))
    if not events:
        logger.info("Nothing to ingest.")
        return
    process(events)
    logger.info("Calendar ingestion complete — %d items sent to pipeline", len(events))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run()
