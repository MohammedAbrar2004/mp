"""
EchoMind Scheduler

Runs Gmail ingestion, Calendar ingestion, and the Preprocessing pipeline
on configurable intervals defined in system_state.py.

Run from the project root with the mp conda environment active:
    python run_scheduler.py
"""

import os
import sys
import logging
import socket
import subprocess
import time
from datetime import datetime, timedelta
import requests

# ---------------------------------------------------------------------------
# Path / env bootstrap — must happen before any domain imports
# ---------------------------------------------------------------------------

ROOT    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
LOGS    = os.path.join(ROOT, "logs")

sys.path.insert(0, BACKEND)
os.chdir(BACKEND)           # keeps media paths, secrets, DB relative paths working
os.makedirs(LOGS, exist_ok=True)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND, ".env"))

# ---------------------------------------------------------------------------
# Intervals (from system_state.py at project root)
# ---------------------------------------------------------------------------

sys.path.insert(0, ROOT)
from system_state import WAIT_AFTER_INGESTION_MINS, WAIT_AFTER_PREPROCESSING_MINS

# ---------------------------------------------------------------------------
# Logging — console + persistent file
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(LOGS, "scheduler.log"), encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger("echomind.scheduler")
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
REQUIRED_OLLAMA_MODELS = ["mistral:7b-instruct-q4_0", "nomic-embed-text"]

# ---------------------------------------------------------------------------
# Job wrappers
# ---------------------------------------------------------------------------


def _run_gmail():
    from backend.app.connectors.gmail.run_gmail_ingestion import run
    run()


def _run_calendar():
    from backend.app.connectors.calendar.run_calendar_ingestion import run
    run()


def _ensure_ollama() -> bool:
    """Return True if Ollama is running (starts it if needed)."""
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=2):
            logger.info("Ollama already running")
            return True
    except OSError:
        pass

    logger.info("Ollama not detected — starting ollama serve...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(10):
        time.sleep(1)
        try:
            with socket.create_connection(("127.0.0.1", 11434), timeout=1):
                logger.info("Ollama started successfully")
                return True
        except OSError:
            pass

    logger.error("Ollama failed to start after 10 s — skipping preprocessing")
    return False


def _ensure_ollama_models() -> bool:
    """Ensure all required Ollama models are available locally."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        resp.raise_for_status()
        installed = {m.get("name", "") for m in resp.json().get("models", [])}
    except Exception as e:
        logger.error("Failed to inspect Ollama models: %s", e)
        return False

    for model in REQUIRED_OLLAMA_MODELS:
        if model in installed:
            logger.info("Ollama model available: %s", model)
            continue

        logger.info("Ollama model missing: %s — pulling...", model)
        try:
            pull = requests.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": model, "stream": False},
                timeout=600,
            )
            pull.raise_for_status()
            logger.info("Pulled Ollama model: %s", model)
        except Exception as e:
            logger.error("Failed to pull Ollama model '%s': %s", model, e)
            return False

    return True


def _run_preprocessing():
    if not _ensure_ollama():
        return
    if not _ensure_ollama_models():
        logger.error("Required Ollama models unavailable — skipping preprocessing")
        return
    from backend.app.preprocessing.orchestrator.preprocessing_pipeline import (
        run_preprocessing,
    )
    run_preprocessing()


_INGESTION_JOBS = [
    ("Gmail",    _run_gmail),
    ("Calendar", _run_calendar),
]

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def _run_phase(name: str, fn) -> None:
    logger.info("  >> %s", name)
    t0 = time.monotonic()
    try:
        fn()
        logger.info("  << %s done (%.1fs)", name, time.monotonic() - t0)
    except Exception:
        logger.exception("  << %s FAILED", name)


def _wait(minutes: int, reason: str) -> None:
    until = datetime.now() + timedelta(minutes=minutes)
    logger.info("    Waiting %d min %s (until %s)", minutes, reason, until.strftime("%H:%M:%S"))
    time.sleep(minutes * 60)


def main() -> None:
    logger.info("=" * 60)
    logger.info("EchoMind Scheduler started")
    logger.info("  Pattern: Ingestion → %d min wait → Preprocessing → %d min wait → repeat",
                WAIT_AFTER_INGESTION_MINS, WAIT_AFTER_PREPROCESSING_MINS)
    logger.info("=" * 60)

    while True:
        # Phase 1 — Ingestion
        logger.info(">>> Ingestion phase")
        for name, fn in _INGESTION_JOBS:
            _run_phase(name, fn)

        _wait(WAIT_AFTER_INGESTION_MINS, "before preprocessing")

        # Phase 2 — Preprocessing
        logger.info(">>> Preprocessing phase")
        _run_phase("Preprocessing", _run_preprocessing)

        _wait(WAIT_AFTER_PREPROCESSING_MINS, "before next ingestion")


if __name__ == "__main__":
    main()
