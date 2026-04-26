"""
Run only the preprocessing pipeline once with full logs.

Usage:
    python run_preprocessing_once.py
"""

import os
import sys
import logging
import socket
import subprocess
import time

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")

sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

# ---------------------------------------------------------------------------
# Logging (same style as scheduler)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("echomind.preprocessing_runner")

# ---------------------------------------------------------------------------
# Ollama check (for LLM cleaning)
# ---------------------------------------------------------------------------

def ensure_ollama() -> bool:
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

    logger.error("Ollama failed to start — preprocessing may skip LLM cleaning")
    return False

# ---------------------------------------------------------------------------
# Run preprocessing
# ---------------------------------------------------------------------------

def main():
    logger.info("=" * 60)
    logger.info("Running Preprocessing Pipeline (one-time)")
    logger.info("=" * 60)

    ensure_ollama()

    try:
        from backend.app.preprocessing.orchestrator.preprocessing_pipeline import run_preprocessing

        start = time.time()
        run_preprocessing()
        duration = time.time() - start

        logger.info("Preprocessing completed successfully (%.2fs)", duration)

    except Exception:
        logger.exception("Preprocessing FAILED")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()