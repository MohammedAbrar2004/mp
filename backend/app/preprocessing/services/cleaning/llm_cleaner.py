import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# 🔥 CONFIG (optimized for your hardware)
DEFAULT_MODEL = "mistral:7b-instruct-q4_0"
FALLBACK_MODEL = None  # ⚠️ disabled for stability
OLLAMA_URL = "http://localhost:11434/api/chat"

MAX_INPUT_CHARS = 2000
TIMEOUT = 120

_SANITIZE_REJECT = {
    "input:",
    "output:",
    "cleaned text:",
    "you are a text cleaning engine",
    "[inst]",
}

_EMAIL_PROMPT_TEMPLATE = """\
[INST]
You are a strict text cleaning engine.

Your job is to extract ONLY the core message from an email.

STRICT RULES:
- Do NOT summarize
- Do NOT interpret
- Do NOT add information
- REMOVE completely:
  - signatures (e.g., "Best regards", names, job titles)
  - disclaimers
  - unsubscribe links
  - promotional text
  - "Click here" lines
  - social media mentions
  - footers of ANY kind

- KEEP ONLY:
  - the actual message content

- If a line looks like a signature or footer → DELETE it

- Output ONLY the cleaned message
- No labels, no explanations

Input:
{text}
[/INST]
""" 


def _build_prompt(text: str, content_type: str) -> str:
    # 🔥 truncate input (VERY IMPORTANT)
    text = text[:MAX_INPUT_CHARS]

    if content_type == "email":
        return _EMAIL_PROMPT_TEMPLATE.format(text=text)

    return (
        "[INST]\n"
        "You are a strict text cleaning engine.\n\n"
        "Clean the following text.\n"
        "Remove noise and formatting issues.\n"
        "Do NOT summarize, interpret, or add information.\n"
        "Output ONLY cleaned text.\n\n"
        f"Input:\n{text}\n"
        "[/INST]"
    )


def _call_ollama(prompt: str, model: str) -> Optional[str]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "num_predict": 600,
            "temperature": 0.1
        }
    }

    for attempt in range(3):
        try:
            logger.info(f"[LLM] Calling model: {model} (attempt {attempt + 1})")

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            raw = data.get("message", {}).get("content")

            if not raw:
                logger.error(f"[LLM] No content in response. Full body: {data}")
                return None

            logger.info(f"[LLM] Raw response received (len={len(raw)})")
            logger.debug(f"[LLM] Raw response content: {repr(raw[:300])}")

            return raw

        except Exception as e:
            if attempt < 2:
                logger.warning(f"[LLM] Retrying (attempt {attempt + 1}) — Error: {type(e).__name__}: {e}")
                time.sleep(2)
            else:
                logger.error(f"[LLM] Failed after 3 attempts — Last error: {type(e).__name__}: {e}")

    return None


import re

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks emitted by reasoning models (e.g. qwen3)."""
    return _THINK_RE.sub("", text).strip()


def sanitize_output(text: str) -> Optional[str]:
    if not text:
        logger.warning("[SANITIZE] Input is None or empty — returning None")
        return None

    # Strip thinking-model reasoning block before any other check
    text = _strip_thinking(text)
    if not text:
        logger.warning("[SANITIZE] Output was entirely a <think> block — returning None")
        return None

    cleaned = text.strip()

    if not cleaned:
        logger.warning("[SANITIZE] Input is whitespace only — returning None")
        return None

    lowered = cleaned.lower()

    # Hard rejection: prompt leakage
    if "[inst]" in lowered or "you are a text cleaning engine" in lowered:
        logger.warning("[SANITIZE] Rejected — prompt leakage detected")
        logger.debug(f"[SANITIZE] Rejected content (first 200 chars): {repr(cleaned[:200])}")
        return None

    # Soft cleaning: strip known label prefixes
    before = cleaned
    cleaned = re.sub(
        r"^(here is the cleaned (text|message):?|cleaned text:?|output:)\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )
    if cleaned != before:
        logger.info(f"[SANITIZE] Stripped label prefix from output")

    cleaned = cleaned.strip()

    if not cleaned:
        logger.warning("[SANITIZE] Output empty after soft cleaning — returning None")
        return None

    logger.info(f"[SANITIZE] Output accepted (len={len(cleaned)})")
    return cleaned


def clean_with_llm(text: str, content_type: str) -> Optional[str]:
    if not text or not text.strip():
        return None

    prompt = _build_prompt(text, content_type)

    response = _call_ollama(prompt, DEFAULT_MODEL)
    cleaned = sanitize_output(response)

    return cleaned