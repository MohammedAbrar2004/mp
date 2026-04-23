"""
Preprocessing Pipeline — Orchestrator

Purpose:
    Coordinate the execution of all preprocessing services in the correct
    order. This is the single entry point for the preprocessing layer.

Execution Order (as defined in preprocessing_contracts.md):
    1. Media Processing  — extract text from PDF / DOCX / audio files
    2. Cleaning Service  — clean memory_chunks.raw_content
                        — clean media_files.extracted_content
    3. Salience + Embedding — NOT implemented in this phase

Rules:
    - Services MUST NOT call each other directly; all coordination goes
      through this orchestrator.
    - Each row is processed independently; a failure on one row does NOT
      block the others.
    - The orchestrator does NOT contain extraction or cleaning logic.
    - DB reads and writes are the orchestrator's responsibility.
    - Idempotency: trigger conditions are re-checked before each step so
      the pipeline is safe to run multiple times.

DB columns required (run migration add_preprocessing_columns.sql first):
    memory_chunks: content, is_cleaned
    media_files:   cleaned_content, is_cleaned
"""

import logging

from app.db.connection import get_connection, close_connection

from app.preprocessing.services.media.media_service import process_media_file
from app.preprocessing.services.cleaning.cleaning_service import (
    clean_text,
    clean_media_content,
)

logger = logging.getLogger("echomind.preprocessing.pipeline")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_preprocessing() -> None:
    """
    Execute the full preprocessing pipeline for all pending rows.

    Steps:
        1. Media extraction  — fill media_files.extracted_content
        2. Chunk cleaning    — fill memory_chunks.content + is_cleaned
        3. Media cleaning    — fill media_files.cleaned_content + is_cleaned
    """
    logger.info("=== Preprocessing pipeline started ===")

    conn = get_connection()
    try:
        _run_media_extraction(conn)
        2
        # _run_chunk_cleaning(conn)
        # _run_media_cleaning(conn)
    finally:
        close_connection(conn)

    logger.info("=== Preprocessing pipeline complete ===")


# ---------------------------------------------------------------------------
# Step 1 — Media extraction
# ---------------------------------------------------------------------------

def _fetch_unextracted_media(conn) -> list[dict]:
    """Return media_files rows where extracted_content IS NULL."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, local_path, mime_type, media_type
            FROM   media_files
            WHERE  extracted_content IS NULL
            ORDER BY created_at
            """
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        cur.close()


def _update_extracted_content(conn, media_id: str, extracted_content: str) -> None:
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE media_files SET extracted_content = %s WHERE id = %s",
            (extracted_content, media_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _run_media_extraction(conn) -> None:
    """
    For each media_file where extracted_content IS NULL:
    call process_media_file() and write the result back to the DB.
    """
    rows = _fetch_unextracted_media(conn)
    logger.info("Media extraction: %d rows pending", len(rows))

    for row in rows:
        media_id   = row["id"]
        local_path = row["local_path"]
        mime_type  = row["mime_type"] or ""

        try:
            extracted = process_media_file(local_path, mime_type)
            if extracted is None:
                logger.warning("Extraction returned None for media_id=%s (%s)", media_id, local_path)
                continue

            _update_extracted_content(conn, media_id, extracted)
            logger.info("Extracted content for media_id=%s", media_id)

        except Exception as e:
            logger.error("Media extraction failed for media_id=%s: %s", media_id, e)


# ---------------------------------------------------------------------------
# Step 2 — Chunk cleaning
# ---------------------------------------------------------------------------

def _fetch_uncleaned_chunks(conn) -> list[dict]:
    """Return memory_chunks rows where is_cleaned = false."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, raw_content, content_type, metadata
            FROM   memory_chunks
            WHERE  is_cleaned = false
            ORDER BY created_at
            """
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        cur.close()


def _update_chunk_content(conn, chunk_id: str, content: str) -> None:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE memory_chunks
            SET    content    = %s,
                   is_cleaned = true
            WHERE  id = %s
            """,
            (content, chunk_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _run_chunk_cleaning(conn) -> None:
    """
    For each memory_chunk where is_cleaned = false:
    call clean_text() on raw_content and write back content + is_cleaned.
    """
    rows = _fetch_uncleaned_chunks(conn)
    logger.info("Chunk cleaning: %d rows pending", len(rows))

    for row in rows:
        chunk_id    = row["id"]
        raw_content = row["raw_content"] or ""

        try:
            cleaned = clean_text(raw_content)
            _update_chunk_content(conn, chunk_id, cleaned)
            logger.info("Cleaned chunk_id=%s", chunk_id)

        except Exception as e:
            logger.error("Chunk cleaning failed for chunk_id=%s: %s", chunk_id, e)


# ---------------------------------------------------------------------------
# Step 3 — Media cleaning
# ---------------------------------------------------------------------------

def _fetch_uncleaned_media(conn) -> list[dict]:
    """Return media_files rows where is_cleaned = false AND extracted_content IS NOT NULL."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, extracted_content
            FROM   media_files
            WHERE  is_cleaned = false
              AND  extracted_content IS NOT NULL
            ORDER BY created_at
            """
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        cur.close()


def _update_media_cleaned_content(conn, media_id: str, cleaned_content: str) -> None:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE media_files
            SET    cleaned_content = %s,
                   is_cleaned      = true
            WHERE  id = %s
            """,
            (cleaned_content, media_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _run_media_cleaning(conn) -> None:
    """
    For each media_file where is_cleaned = false AND extracted_content IS NOT NULL:
    call clean_media_content() and write back cleaned_content + is_cleaned.
    """
    rows = _fetch_uncleaned_media(conn)
    logger.info("Media cleaning: %d rows pending", len(rows))

    for row in rows:
        media_id          = row["id"]
        extracted_content = row["extracted_content"] or ""

        try:
            cleaned = clean_media_content(extracted_content)
            if cleaned is None:
                logger.warning("Cleaning returned None for media_id=%s", media_id)
                continue

            _update_media_cleaned_content(conn, media_id, cleaned)
            logger.info("Cleaned media_id=%s", media_id)

        except Exception as e:
            logger.error("Media cleaning failed for media_id=%s: %s", media_id, e)
