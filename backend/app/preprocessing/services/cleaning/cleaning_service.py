import logging

from .text_cleaning import clean_text_content
from .email_cleaning import clean_email_content
from .media_cleaning import clean_media_content
from .heuristic_rules import heuristic_clean

logger = logging.getLogger(__name__)


def clean_content(raw_text: str, content_type: str) -> str:
    if not raw_text:
        return ""

    logger.info(f"Cleaning content type: {content_type}")

    try:
        if content_type == "text":
            return clean_text_content(raw_text)

        elif content_type == "email":
            return clean_email_content(raw_text)

        elif content_type in ("document", "audio"):
            return clean_media_content(raw_text)

        else:
            logger.warning(f"Unknown content_type '{content_type}', using heuristic fallback")
            return heuristic_clean(raw_text)

    except Exception:
        logger.exception(f"Cleaning failed for content_type '{content_type}', returning original")
        return raw_text
