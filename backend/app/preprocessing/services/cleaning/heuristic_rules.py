import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Bullet normalization
_BULLET_RE = re.compile(r"[•●◦▸▶►‣⁃]")

# Spacing rules
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


def heuristic_clean(text: str) -> str:
    if not text:
        return ""

    # Normalize unicode (safe)
    text = unicodedata.normalize("NFC", text)

    # Normalize bullet characters
    text = _BULLET_RE.sub("-", text)

    # 🔥 FIX: Remove ONLY junk clusters (3+ symbols), preserve emojis
    text = re.sub(r"[^\w\s.,!?'\"\-]{3,}", "", text)

    # Normalize spaces
    text = _MULTI_SPACE_RE.sub(" ", text)

    # Normalize newlines
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)

    return text.strip()


def compute_noise_score(text: str) -> float:
    if not text:
        return 0.0

    total_chars = len(text)
    tokens = text.split()
    total_tokens = len(tokens)
    lines = text.splitlines()
    total_lines = len(lines)

    # Special characters (excluding spaces)
    special_char_ratio = (
        sum(1 for c in text if not c.isalnum() and not c.isspace()) / total_chars
        if total_chars > 0 else 0.0
    )

    short_token_ratio = (
        sum(1 for t in tokens if len(t) <= 2) / total_tokens
        if total_tokens > 0 else 0.0
    )

    whitespace_hits = len(re.findall(r" {3,}", text))
    whitespace_penalty = min(whitespace_hits / (total_chars / 100 + 1), 1.0)

    line_fragmentation = (
        sum(1 for l in lines if len(l.strip()) < 5) / total_lines
        if total_lines > 0 else 0.0
    )

    score = (
        special_char_ratio * 0.4 +
        short_token_ratio * 0.3 +
        whitespace_penalty * 0.2 +
        line_fragmentation * 0.1
    )

    score = max(0.0, min(1.0, score))

    logger.info(f"Noise score: {score:.2f}")
    return score


def is_readable(text: str) -> bool:
    if not text:
        return False

    words = text.split()
    total_words = len(words)

    if total_words == 0:
        return False

    # 🔥 FIX: only count real words (avoid symbols/emojis)
    valid_words = sum(1 for w in words if len(w) > 2 and w.isalpha())

    readable = (valid_words / total_words) > 0.6

    logger.info(f"Readable: {readable}")
    return readable


def should_use_llm(text: str) -> bool:
    noise = compute_noise_score(text)
    readable = is_readable(text)

    # 🔥 FIX: slightly lowered threshold for OCR detection
    if noise > 0.28 and not readable:
        return True

    return False