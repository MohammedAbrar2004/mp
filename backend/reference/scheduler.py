"""
Standalone scheduler for EchoMind.
Triggers ingestion for all pull-based connectors on a configurable interval.
WhatsApp is push-based and is NOT triggered here.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

from pipelines.ingestion_pipeline import run_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("EchoMind.Scheduler")


def scheduled_job():
    logger.info("Scheduler triggered — running ingestion pipeline")
    try:
        run_ingestion()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")


if __name__ == "__main__":
    interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "30"))

    scheduler = BlockingScheduler()
    scheduler.add_job(
        scheduled_job,
        trigger=IntervalTrigger(minutes=interval),
        id="ingestion_job",
        name="EchoMind Ingestion",
        replace_existing=True,
    )

    logger.info(f"Scheduler started — interval: {interval} minutes")
    logger.info("WhatsApp is push-based — handled by Node.js service independently")

    try:
        scheduled_job()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
