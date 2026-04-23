"""
Cleaning Service — Preprocessing Layer

Purpose:
    Convert raw text into clean, structured content ready for salience
    scoring and embedding generation.

Inputs:
    For memory_chunks:
        raw_content  (str):  Original ingested text from the connector.
        content_type (str):  Source type (e.g. 'whatsapp', 'gmail', 'calendar').
        metadata     (dict): Chunk metadata (source, timestamps, etc.).

    For media_files:
        extracted_content (str): Raw text extracted by the media processor.

Outputs:
    For memory_chunks:
        content    (str):  Cleaned, structured text.
        is_cleaned (bool): Set to True after successful cleaning.

    For media_files:
        cleaned_content (str):  Cleaned version of extracted_content.
        is_cleaned      (bool): Set to True after successful cleaning.

Behavior:
    - Removes HTML tags, email signatures, and formatting noise.
    - Normalizes whitespace and line breaks.
    - Generic cleaning — NOT email-specific or source-specific.
    - Primary model: local LLM (Ollama / mistral:7b-instruct-q4_0).
    - Fallback: returns original raw_text unchanged.
    - Does NOT merge media content into memory_chunks.content.
    - Does NOT modify raw_content or extracted_content.
    - Idempotent: if is_cleaned = true, skip processing (enforced by orchestrator).
    - On failure: logs error, returns original text as fallback.

Trigger Conditions (enforced by orchestrator):
    memory_chunks: is_cleaned = false
    media_files:   is_cleaned = false AND extracted_content IS NOT NULL
"""

import logging

import requests

logger = logging.getLogger("echomind.preprocessing.cleaning")

_OLLAMA_URL = "http://localhost:11434/api/generate"
_MODEL = "mistral:7b-instruct-q4_0"
_MAX_RETRIES = 3

# Content types that always go through LLM regardless of length/complexity
_ALWAYS_CLEAN_TYPES = {"email", "gmail", "document", "audio"}

# Prefixes the LLM sometimes prepends to its output despite instructions
_OUTPUT_PREFIXES = [
    "here's the cleaned text:",
    "here is the cleaned text:",
    "cleaned text:",
    "output:",
]

# Strings that indicate prompt leakage — output is discarded if found
_LEAKAGE_MARKERS = [
    "you are a text cleaning engine",
    "input:",
    "do not summarize",
    "do not change meaning",
    "return only",
]


def is_simple_text(text: str) -> bool:
    """
    Return True if text is short and plain enough to skip LLM cleaning.

    Criteria (ALL must be true):
    - length < 200 characters
    - no email address pattern (@)
    - no URL (http)
    - no multiple consecutive line breaks
    """
    if len(text) >= 200:
        return False
    if "@" in text:
        return False
    if "http" in text:
        return False
    if "\n\n" in text:
        return False
    return True


def _build_prompt(raw_text: str) -> str:
    return (
        "[INST] Clean the following text. "
        "Remove noise, formatting issues, email signatures, headers, and junk text. "
        "Do NOT summarize. Do NOT change meaning. Do NOT add new information. "
        "Return ONLY the cleaned text. "
        "Do NOT include instructions, labels, or explanations. "
        "Do NOT include labels like 'Input:' or 'Output:'. "
        "Do NOT repeat the prompt. "
        "Your entire response must be the cleaned text and nothing else.\n\n"
        f"{raw_text} [/INST]"
    )


def _strip_output_prefixes(text: str) -> str:
    """Remove common prefixes the LLM prepends despite instructions."""
    lower = text.lower()
    for prefix in _OUTPUT_PREFIXES:
        if lower.startswith(prefix):
            return text[len(prefix):].lstrip()
    return text


def _sanitize(llm_output: str) -> str | None:
    """
    Return cleaned llm_output if it passes quality checks, else None.

    Strips output prefixes, then checks for leakage markers.
    Returns None to trigger raw_text fallback.
    """
    cleaned = _strip_output_prefixes(llm_output.strip())

    if not cleaned:
        logger.warning("LLM returned empty output — falling back to raw text")
        return None

    lower = cleaned.lower()
    for marker in _LEAKAGE_MARKERS:
        if marker in lower:
            logger.warning("Prompt leakage detected ('%s') — falling back to raw text", marker)
            return None

    return cleaned


def _call_ollama(prompt: str) -> str | None:
    payload = {"model": _MODEL, "prompt": prompt, "stream": False}

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.post(_OLLAMA_URL, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.RequestException as e:
            if attempt < _MAX_RETRIES:
                logger.warning("Ollama call failed (attempt %d/%d): %s", attempt, _MAX_RETRIES, e)
            else:
                logger.error("Ollama call failed after %d attempts: %s", _MAX_RETRIES, e)

    return None


def _llm_clean(raw_text: str) -> str:
    """Call Ollama, sanitize output, fallback to raw_text on any problem."""
    llm_output = _call_ollama(_build_prompt(raw_text))

    if llm_output is None:
        logger.warning("LLM unavailable — falling back to raw text")
        return raw_text

    sanitized = _sanitize(llm_output)
    if sanitized is None:
        return raw_text

    return sanitized


def clean_text(raw_text: str, force_llm: bool = False) -> str:
    """
    Clean arbitrary raw text.

    Uses LLM only when necessary:
    - Always skips empty input.
    - Returns simple text unchanged (heuristic: short, no URLs/emails/multiline).
    - Uses LLM for complex text or when force_llm=True.

    Falls back to raw_text if LLM is unavailable or output contains leakage.

    Args:
        raw_text:  Any raw text string to clean.
        force_llm: Skip heuristic check and always use LLM (used for emails,
                   documents, and audio transcriptions).

    Returns:
        Cleaned text string (never None).
    """
    if not raw_text or not raw_text.strip():
        return raw_text

    if not force_llm and is_simple_text(raw_text):
        logger.debug("Simple text detected — skipping LLM")
        return raw_text

    return _llm_clean(raw_text)


def clean_chunk_content(
    raw_content: str,
    content_type: str,
    metadata: dict,
) -> str | None:
    """
    Clean raw_content from a memory_chunk row.

    Email, document, and audio content always go through LLM.
    Other types use the heuristic to decide.

    Args:
        raw_content:  Original ingested text.
        content_type: Source type identifier (e.g. 'whatsapp', 'gmail').
        metadata:     Chunk metadata dict.

    Returns:
        Cleaned content string, or None if cleaning fails.
    """
    try:
        force = (content_type or "").lower() in _ALWAYS_CLEAN_TYPES
        return clean_text(raw_content, force_llm=force)
    except Exception as e:
        logger.error("clean_chunk_content failed: %s", e)
        return None


def clean_media_content(extracted_content: str) -> str | None:
    """
    Clean extracted_content from a media_file row.

    Media content always goes through LLM (extracted from PDF/DOCX/audio).

    Args:
        extracted_content: Raw text output from a media processor.

    Returns:
        Cleaned content string, or None if cleaning fails.
    """
    try:
        return clean_text(extracted_content, force_llm=True)
    except Exception as e:
        logger.error("clean_media_content failed: %s", e)
        return None
