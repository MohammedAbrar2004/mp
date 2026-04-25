import logging

from app.connectors.gmail.client import fetch_recent_emails
from pipelines.ingestion_pipeline import process

logger = logging.getLogger("echomind.ingestion.gmail")


def run():
    logger.info("Fetching emails (limit=50)...")
    emails = fetch_recent_emails(limit=50)
    logger.info("Fetched %d emails", len(emails))
    if not emails:
        logger.info("Nothing to ingest.")
        return
    process(emails)
    logger.info("Gmail ingestion complete — %d items sent to pipeline", len(emails))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run()
