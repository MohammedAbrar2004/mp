import logging
import re

from .heuristic_rules import heuristic_clean

logger = logging.getLogger(__name__)

_PAGE_NUM_RE = re.compile(
    r"^\s*(page\s+\d+(\s+of\s+\d+)?|-\s*\d+\s*-|\d+)\s*$",
    re.IGNORECASE,
)
_SEPARATOR_RE = re.compile(r"^[\-_=]{3,}\s*$")


def clean_media_content(text: str) -> str:
    if not text or not text.strip():
        return ""

    logger.info("Cleaning media content")

    text = heuristic_clean(text)

    lines = text.splitlines()
    lines = [l for l in lines if not _PAGE_NUM_RE.match(l) and not _SEPARATOR_RE.match(l)]
    text = "\n".join(l.strip() for l in lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
