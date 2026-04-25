import logging

from .heuristic_rules import heuristic_clean
from .emoji_normalization import normalize_emojis

logger = logging.getLogger(__name__)


def clean_text_content(text: str) -> str:
    if not text:
        return text or ""

    logger.info("Cleaning text content")

    try:
        text = heuristic_clean(text)
        text = normalize_emojis(text)
    except Exception:
        logger.exception("heuristic/emoji cleaning failed, returning original")
        return text

    return text
