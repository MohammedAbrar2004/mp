"""
Preprocessing runner — manual execution entry point.

Run from backend/:
    python -m app.preprocessing.orchestrator.run_preprocessing

Prerequisites:
    1. conda activate mp
    2. DB migration applied:
           psql -d mp -f app/db/migrations/add_preprocessing_columns.sql
    3. Ollama running with mistral:7b-instruct-q4_0 loaded
"""

import logging
import sys
import os

# Allow running from repo root or backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

from app.preprocessing.orchestrator.preprocessing_pipeline import run_preprocessing

if __name__ == "__main__":
    run_preprocessing()
