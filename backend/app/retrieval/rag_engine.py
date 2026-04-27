import json
import logging
import os
from typing import Any

import psycopg2.extras
import requests
from dotenv import load_dotenv

from app.preprocessing.services.embedding.embedding_service import generate_embedding

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"), override=True)

logger = logging.getLogger("echomind.retrieval.rag")

GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY_ENV = "GROQ_API_KEY"
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_TIMEOUT_SECONDS = int(os.getenv("RAG_TIMEOUT_SECONDS", "120"))
MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "12000"))


def _resolve_groq_api_key(conn, user_id: str | None = None) -> str | None:
    env_key = os.getenv(GROQ_API_KEY_ENV)
    if env_key:
        return env_key

    if not user_id:
        return None

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT api_keys FROM user_settings WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()

    api_keys = (row or {}).get("api_keys") or {}
    return (
        api_keys.get("groq_api_key")
        or api_keys.get("groq")
        or api_keys.get("openai_api_key")
    )


def retrieve(query: str, conn, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    query_embedding = generate_embedding(query)
    if query_embedding is None:
        logger.warning("Skipping retrieval because query embedding failed")
        return []

    vector_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT mc.id,
                   mc.timestamp,
                   mc.content,
                   mc.title,
                   mc.summary,
                   mc.participants,
                   mc.content_type,
                   mc.refined_salience,
                   ds.name AS connector_source,
                   (1 - (mc.embedding <=> %s::vector)) AS vector_similarity,
                   (
                       (0.7 * (1 - (mc.embedding <=> %s::vector))) +
                       (0.3 * COALESCE(mc.refined_salience, mc.initial_salience, 0))
                   ) AS weighted_score
            FROM memory_chunks mc
            JOIN data_sources ds ON ds.id = mc.source_id
            WHERE mc.is_deleted = false
              AND mc.embedding IS NOT NULL
            ORDER BY weighted_score DESC
            LIMIT %s
            """,
            (vector_literal, vector_literal, top_k),
        )
        return [dict(r) for r in cur.fetchall()]


def build_context(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return ""

    blocks: list[str] = []
    total_chars = 0
    for chunk in chunks:
        participants = chunk.get("participants") or []
        if isinstance(participants, str):
            try:
                participants = json.loads(participants)
            except Exception:
                participants = [participants]

        block = (
            f"Source: {chunk.get('connector_source', 'unknown')}\n"
            f"Timestamp: {chunk.get('timestamp')}\n"
            f"Participants: {participants}\n"
            f"Title: {chunk.get('title') or ''}\n"
            f"Summary: {chunk.get('summary') or ''}\n"
            f"Content:\n{(chunk.get('content') or '')}\n"
            "-----"
        )

        if total_chars + len(block) > MAX_CONTEXT_CHARS:
            break

        blocks.append(block)
        total_chars += len(block)

    return "\n".join(blocks)


def generate_answer(query: str, context: str, api_key: str | None) -> str:
    if not context.strip():
        return "I don't have information about that in your memory yet."

    if not api_key:
        logger.error("GROQ API key missing; cannot generate response")
        return (
            "I found relevant memory chunks, but answer generation is unavailable "
            "because GROQ API key is not configured."
        )

    system_prompt = (
        "You are EchoMind, a personal memory assistant. "
        "Answer only from the provided memory context. "
        "If context is insufficient, say exactly: "
        "\"I don't have information about that in your memory yet.\" "
        "Be concise and cite source snippets naturally."
    )
    user_prompt = (
        f"User query:\n{query}\n\n"
        f"Memory context:\n{context}\n\n"
        "Return a helpful answer grounded only in memory context."
    )

    payload = {
        "model": GROQ_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "top_p": 0.95,
        "max_tokens": 1200,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=RAG_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
        if not text:
            logger.error("GROQ chat response missing content: %s", data)
            return "I couldn't generate a response right now."
        return text.strip()
    except Exception as exc:
        logger.error("GROQ chat completion failed: %s", exc)
        return "I couldn't generate a response right now."


def query_pipeline(query_text: str, conn, user_id: str | None = None) -> tuple[str, list[str]]:
    chunks = retrieve(query_text, conn, top_k=DEFAULT_TOP_K)
    context = build_context(chunks)
    api_key = _resolve_groq_api_key(conn, user_id=user_id)
    answer = generate_answer(query_text, context, api_key=api_key)
    source_ids = [str(chunk["id"]) for chunk in chunks if chunk.get("id")]
    return answer, source_ids
