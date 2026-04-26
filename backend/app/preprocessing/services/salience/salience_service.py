"""
Salience Service — Preprocessing Layer
"""

import re
import logging

logger = logging.getLogger(__name__)

# -----------------------------
# Signals
# -----------------------------
_ACTION_KEYWORDS = frozenset([
    "meeting", "deadline", "task", "important", "urgent", "review",
    "action", "follow up", "reminder", "schedule", "appointment",
    "due", "asap", "call", "confirm", "submit",
])

_ACTION_VERBS = ["need", "will", "should", "have to", "must", "plan", "handle"]

_PROGRESS_WORDS = ["completed", "done", "finished", "working", "started"]

_TIME_WORDS = ["today", "tomorrow", "tonight"]

_DATE_RE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*)\b",
    re.IGNORECASE,
)


# -----------------------------
# Main Function
# -----------------------------
def compute_salience(
    content: str,
    metadata: dict,
    has_media: bool,
) -> float | None:
    try:
        if not content or not content.strip():
            return 0.0

        score = 0.15  # small base boost
        lower = content.lower()

        # -----------------------------
        # Length signal
        # -----------------------------
        length = len(content)
        if length > 300:
            score += 0.40
        elif length > 100:
            score += 0.25
        elif length > 30:
            score += 0.20

        # -----------------------------
        # Keyword signal
        # -----------------------------

        keyword_hits = sum(1 for kw in _ACTION_KEYWORDS if kw in lower)
        if keyword_hits >= 3:
            score += 0.40
        elif keyword_hits >= 1:
            score += 0.35

        # -----------------------------
        # Action verbs
        # -----------------------------
        if any(v in lower for v in _ACTION_VERBS):
            score += 0.25

        # -----------------------------
        # Progress signals (NEW)
        # -----------------------------
        if any(p in lower for p in _PROGRESS_WORDS):
            score += 0.20

        if "deadline" in lower:
            score += 0.25
        # -----------------------------
        # Time signals
        # -----------------------------
        if any(t in lower for t in _TIME_WORDS):
            score += 0.20

        if _DATE_RE.search(content):
            score += 0.20

        # -----------------------------
        # Media signal (boosted)
        # -----------------------------
        if has_media:
            score += 0.25

        return min(round(score, 3), 1.0)

    except Exception:
        logger.exception("Salience scoring failed")
        return None