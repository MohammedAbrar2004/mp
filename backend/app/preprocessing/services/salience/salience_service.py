"""
Salience Service — Preprocessing Layer

Purpose:
    Assign an initial importance score (0.0–1.0) to each memory_chunk.
    This score controls whether a chunk is forwarded to the semantic layer.

Input:
    content       (str):  Cleaned text from memory_chunks.content.
    metadata      (dict): Chunk metadata (source, timestamps, participants, etc.).
    has_media     (bool): Whether the chunk has associated media_files rows.

Output:
    initial_salience (float): Importance score in range [0.0, 1.0].
                              Returns None on failure.

Behavior:
    Heuristics (initial implementation):
        - Content length: longer content → higher base score.
        - Keyword presence: action words, names, dates → boost.
        - Media presence: chunks with attachments → boost.
    - Does NOT write to the database directly.
    - Does NOT call other services.
    - Stateless and idempotent.
    - On failure: logs error and returns None (orchestrator handles retry).

Trigger Condition (enforced by orchestrator):
    is_cleaned = true
    AND is_salience_computed = false
"""

import re
import logging

logger = logging.getLogger(__name__)

_ACTION_KEYWORDS = frozenset([
    "meeting", "deadline", "task", "important", "urgent", "review",
    "action", "follow up", "reminder", "schedule", "appointment",
    "due", "asap", "call", "confirm", "submit",
])

_DATE_RE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*)\b",
    re.IGNORECASE,
)


def compute_salience(
    content: str,
    metadata: dict,
    has_media: bool,
) -> float | None:
    """
    Compute an initial salience score for a memory_chunk.

    Args:
        content:   Cleaned text (memory_chunks.content).
        metadata:  Chunk metadata dict.
        has_media: True if the chunk has one or more linked media_files rows.

    Returns:
        Float score in [0.0, 1.0], or None if computation fails.
    """
    try:
        if not content or not content.strip():
            return 0.0

        score = 0.0
        lower = content.lower()

        # Length signal
        length = len(content)
        if length > 300:
            score += 0.30
        elif length > 100:
            score += 0.15
        elif length > 30:
            score += 0.05

        # Keyword signal
        keyword_hits = sum(1 for kw in _ACTION_KEYWORDS if kw in lower)
        if keyword_hits >= 3:
            score += 0.30
        elif keyword_hits >= 1:
            score += 0.20

        # Date/time pattern signal
        if _DATE_RE.search(content):
            score += 0.20

        # Media attachment signal
        if has_media:
            score += 0.15

        return min(round(score, 3), 1.0)

    except Exception:
        logger.exception("Salience scoring failed")
        return None
