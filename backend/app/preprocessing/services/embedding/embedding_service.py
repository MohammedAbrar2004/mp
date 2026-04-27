"""
Embedding Service — Preprocessing Layer

Purpose:
    Convert cleaned text content into a dense vector embedding for
    semantic search and similarity operations in the retrieval layer.

Input:
    content (str): Cleaned text from memory_chunks.content.

Output:
    embedding (list[float]): Dense vector representation of the content.
                             Returns None on failure.

Behavior:
    - Uses a local embedding model (exact model configured separately).
    - Does NOT write to the database directly.
    - Does NOT call other services.
    - Stateless and idempotent.
    - On failure: logs error and returns None (orchestrator handles retry).

Trigger Condition (enforced by orchestrator):
    content IS NOT NULL
    AND embedding IS NULL
"""


import logging
import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger("echomind.preprocessing.embedding")

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

OLLAMA_EMBED_URL = os.getenv(
    "OLLAMA_EMBED_URL", "http://localhost:11434/v1/embeddings"
)
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
MAX_INPUT_CHARS = 8000
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def generate_embedding(content: str) -> list[float] | None:
    """
    Generate a vector embedding for a cleaned content string.

    Args:
        content: Cleaned text (memory_chunks.content).

    Returns:
        Dense float vector as a list, or None if generation fails.
    """
    if not content or not content.strip():
        return None

    text = content[:MAX_INPUT_CHARS]
    payload = {"model": OLLAMA_EMBED_MODEL, "input": text}

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            embedding: Optional[list[float]] = ((data.get("data") or [{}])[0]).get(
                "embedding"
            )

            if not embedding:
                logger.error("Embedding response missing vector: %s", data)
                return None

            return embedding
        except Exception as exc:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    "Embedding call failed (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error("Embedding call failed after retries: %s", exc)

    return None
