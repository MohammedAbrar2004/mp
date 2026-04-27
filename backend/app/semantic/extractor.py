import logging
import re
import time
import requests
from typing import Optional
from datetime import datetime

logger = logging.getLogger("echomind.semantic.extractor")

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "mistral:7b-instruct-q4_0"
TIMEOUT = 120
MAX_INPUT_CHARS = 3000
MAX_RETRIES = 3
RETRY_DELAY = 5


def build_prompt(text: str, participants: list, timestamp: str) -> str:
    text_truncated = text[:MAX_INPUT_CHARS]
    participants_str = ", ".join(participants) if participants else "unknown"

    prompt = f"""[INST]
You are a semantic knowledge extractor for a personal memory assistant called EchoMind.

EchoMind ingests messages from WhatsApp, Gmail, Google Calendar, and manual notes. Your job is to extract structured knowledge from a single chunk of text and return STRICTLY VALID JSON.

CRITICAL OUTPUT RULES:
- Output ONLY valid JSON. Nothing else.
- No explanations, no markdown, no text outside the JSON.
- No trailing commas. Double quotes only.
- If you are unsure → use [] or null.

---

TEXT:
{text_truncated}

PARTICIPANTS: {participants_str}
TIMESTAMP: {timestamp}

---

EXTRACTION RULES:

## Entities
Extract ONLY entities explicitly named or clearly referenced in the text. Do not guess.

Types and real examples from this project:
- person       → abrar, amaan, abdullah, ma'am, hadi
- project      → echomind
- organization → university, anthropic
- tool         → whatsapp, gmail, google-meet, ollama, github
- technology   → pgvector, postgresql, fastapi, whisper, mistral, pydantic, psycopg2
- file         → architecture_report.pdf, notes_day1.docx, api_spec.pdf
- location     → lab, ma'am's office, canteen, online
- concept      → salience, embedding, preprocessing, semantic-search, ingestion
- topic        → authentication, deployment, testing, demo
- task         → demo-prep, schema-migration, search-ranking-fix

## Event
Extract ONE meaningful event if present. Use null if the text is a casual message, reaction, or has no event.

Event types: decision, meeting, task, discussion, milestone, other

Event title: 3–7 words, specific (e.g. "demo rehearsal scheduled for thursday")
Event summary: 5–10 words describing what specifically happened

Keywords: exactly 3 lowercase single-word strings most relevant to the chunk. Only when event is not null.

## Relationships
Link participants and named entities to the event. Only include entities that appear in the text.

Roles: participant, subject, organizer, mentioned, owner, assignee, reporter

## Refined Salience
Score the chunk's importance from 0.0 to 1.0:
- 0.9 → hard deadline + assigned action ("submit by thursday", "abrar must fix X by end of day")
- 0.8 → confirmed meeting with time, task with deadline, decision with clear outcome
- 0.7 → task discussion, progress update with clear next step or action item
- 0.5 → informational update, general team discussion, no immediate action
- 0.3 → one-liner acknowledgement ("ok", "on it", "pulled, looks clean", "sounds good")
- 0.1 → pure noise, emoji-only, no extractable information

---

EXAMPLE (WhatsApp group message):
Text: "Quick reminder, we have a meeting with Ma'am tomorrow at 11. Make sure the demo is running before we go in."
Participants: abrar, amaan, abdullah
Timestamp: 2026-04-22T15:30:00+05:30

Output:
{{
  "entities": [
    {{"name": "ma'am", "type": "person"}},
    {{"name": "echomind", "type": "project"}}
  ],
  "event": {{
    "title": "meeting with ma'am tomorrow at 11",
    "summary": "team reminded to have demo ready before meeting",
    "event_type": "meeting",
    "timestamp": "2026-04-22T15:30:00+05:30",
    "keywords": ["meeting", "demo", "deadline"]
  }},
  "relationships": [
    {{"entity": "abrar", "role": "participant"}},
    {{"entity": "amaan", "role": "participant"}},
    {{"entity": "abdullah", "role": "participant"}},
    {{"entity": "ma'am", "role": "organizer"}}
  ],
  "refined_salience": 0.8
}}

---

Now extract from the TEXT above. Return ONLY the JSON object.
[/INST]"""

    return prompt


def _call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "num_predict": 1200,
            "temperature": 0.1,
        },
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content")

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.debug(f"Ollama attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Ollama call failed after {MAX_RETRIES} attempts: {e}")
                return None

    return None


def _sanitize_output(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"\[inst\].*?\[/inst\]", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r"^(here is|output|result|response|extracted|cleaned)[\s:]*",
        "",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    text = text.strip()

    json_start = text.find("{")
    json_end = text.rfind("}")

    if json_start != -1 and json_end != -1:
        text = text[json_start:json_end + 1]

    return text.strip()


def extract(semantic_input: dict) -> Optional[str]:
    text = semantic_input.get("text", "")
    participants = semantic_input.get("participants", [])
    timestamp = semantic_input.get("timestamp", datetime.utcnow().isoformat())

    logger.info(f"Extracting: text_len={len(text)} participants={participants}")

    prompt = build_prompt(text, participants, timestamp)
    raw_output = _call_ollama(prompt)

    if not raw_output:
        logger.warning("Ollama returned None")
        return None

    logger.info(f"Raw output: {len(raw_output)} chars")
    logger.debug(f"Raw: {raw_output[:300]}")

    sanitized = _sanitize_output(raw_output)

    logger.debug(f"Sanitized: {sanitized[:300]}")

    if not sanitized:
        logger.warning("Sanitized output is empty")
        return None

    if not sanitized.startswith("{") or not sanitized.endswith("}"):
        logger.warning(
            f"Output not valid JSON structure — starts='{sanitized[:20]}' ends='{sanitized[-20:]}'"
        )
        return None

    return sanitized
