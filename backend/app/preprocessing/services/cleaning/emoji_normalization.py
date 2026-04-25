import logging
import re

logger = logging.getLogger(__name__)

EMOJI_MAP = {
    "👍": " good",
    "✅": " completed",
    "❗": " important",
    "🔥": " important",
    "😂": " funny",
    "🙏": " thanks",
}


def normalize_emojis(text: str) -> str:
    if not text:
        return text or ""

    for emoji, replacement in EMOJI_MAP.items():
        text = text.replace(emoji, replacement)

    text = re.sub(r"\s{2,}", " ", text)
    return text
