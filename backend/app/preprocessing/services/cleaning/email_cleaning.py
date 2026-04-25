import logging
import re

from bs4 import BeautifulSoup

from backend.app.preprocessing.services.cleaning.emoji_normalization import normalize_emojis

from .heuristic_rules import heuristic_clean
from .llm_cleaner import clean_with_llm

logger = logging.getLogger(__name__)


def clean_email_content(raw_html: str) -> str:
    if not raw_html or not raw_html.strip():
        return ""

    logger.info("Cleaning email content")

    # Step 1 — HTML → plain text
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator="\n")

    logger.info(f"Email length (raw): {len(text)}")

    # Step 2 — Heuristic cleaning
    text = heuristic_clean(text)

    # Step 3 — Pre-clean (reduce LLM burden)

    # remove URLs
    text = re.sub(r"http\S+", "", text)

    # remove unsubscribe lines
    text = re.sub(r"unsubscribe.*", "", text, flags=re.IGNORECASE)

    # remove "click here" lines
    text = re.sub(r"click here.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"follow us.*", "", text, flags=re.IGNORECASE)

    # normalize spacing again after removals
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    text = normalize_emojis(text)

    logger.info(f"Email length (pre-cleaned): {len(text)}")

    # Step 4 — LLM cleaning (sanitize_output is applied inside clean_with_llm)
    cleaned = clean_with_llm(text, content_type="email")

    # Step 5 — Fallback (IMPORTANT)
    if not cleaned:
        logger.warning("LLM failed or returned invalid output — using heuristic result")
        return text

    return cleaned