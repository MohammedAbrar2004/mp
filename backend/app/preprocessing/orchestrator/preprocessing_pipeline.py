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
import time
from datetime import datetime, timezone

from app.db.connection import get_connection, close_connection

from app.preprocessing.services.media.media_service import process_media_file
from app.preprocessing.services.cleaning.cleaning_service import clean_content
from app.preprocessing.services.cleaning.media_cleaning import clean_media_content
from app.preprocessing.services.salience.salience_service import compute_salience

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
        4. Salience scoring  — fill memory_chunks.initial_salience + is_salience_computed
    """
    batch_cutoff = datetime.now(timezone.utc)
    logger.info("=== Preprocessing pipeline started (cutoff %s) ===", batch_cutoff.strftime("%H:%M:%S"))

    conn = get_connection()
    try:
        _run_media_extraction(conn, batch_cutoff)
        _run_chunk_cleaning(conn, batch_cutoff)
        _run_media_cleaning(conn, batch_cutoff)
        _run_salience_scoring(conn, batch_cutoff)
    finally:
        close_connection(conn)

    logger.info("=== Preprocessing pipeline complete ===")


# ---------------------------------------------------------------------------
# Step 1 — Media extraction
# ---------------------------------------------------------------------------

def _fetch_unextracted_media(conn, cutoff) -> list[dict]:
    """Return media_files rows where extracted_content IS NULL and created before cutoff."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, local_path, mime_type, media_type
            FROM   media_files
            WHERE  extracted_content IS NULL
              AND  created_at < %s
            ORDER BY created_at
            """,
            (cutoff,),
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


def _run_media_extraction(conn, cutoff) -> None:
    """
    For each media_file where extracted_content IS NULL:
    call process_media_file() and write the result back to the DB.
    """
    rows = _fetch_unextracted_media(conn, cutoff)
    logger.info("Media extraction: %d rows pending", len(rows))
    if not rows:
        return

    ok = fail = skipped = 0
    t0 = time.monotonic()

    for row in rows:
        media_id   = row["id"]
        local_path = row["local_path"]
        mime_type  = row["mime_type"] or ""

        try:
            extracted = process_media_file(local_path, mime_type)
            if extracted is None:
                logger.warning("  extraction returned None for media_id=%s (%s)", media_id, local_path)
                skipped += 1
                continue

            _update_extracted_content(conn, media_id, extracted)
            logger.debug("  extracted media_id=%s", media_id)
            ok += 1

        except Exception as e:
            logger.error("  FAILED media_id=%s: %s", media_id, e)
            fail += 1

    logger.info(
        "Media extraction done: %d ok, %d skipped, %d failed (%.1fs)",
        ok, skipped, fail, time.monotonic() - t0,
    )


# ---------------------------------------------------------------------------
# Step 2 — Chunk cleaning
# ---------------------------------------------------------------------------

def _fetch_uncleaned_chunks(conn, cutoff) -> list[dict]:
    """Return memory_chunks rows where is_cleaned = false and created before cutoff."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, raw_content, content_type, metadata
            FROM   memory_chunks
            WHERE  is_cleaned = false
              AND  created_at < %s
            ORDER BY created_at
            """,
            (cutoff,),
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


def _run_chunk_cleaning(conn, cutoff) -> None:
    """
    For each memory_chunk where is_cleaned = false:
    call clean_content() on raw_content and write back content + is_cleaned.
    """
    rows = _fetch_uncleaned_chunks(conn, cutoff)
    logger.info("Chunk cleaning: %d rows pending", len(rows))
    if not rows:
        return

    ok = fail = 0
    t0 = time.monotonic()

    for row in rows:
        chunk_id    = row["id"]
        raw_content = row["raw_content"] or ""

        try:
            cleaned = clean_content(raw_content, row["content_type"])
            _update_chunk_content(conn, chunk_id, cleaned)
            logger.debug("  cleaned chunk_id=%s", chunk_id)
            ok += 1

        except Exception as e:
            logger.error("  FAILED chunk_id=%s: %s", chunk_id, e)
            fail += 1

    logger.info(
        "Chunk cleaning done: %d ok, %d failed (%.1fs)",
        ok, fail, time.monotonic() - t0,
    )


# ---------------------------------------------------------------------------
# Step 3 — Media cleaning
# ---------------------------------------------------------------------------

def _fetch_uncleaned_media(conn, cutoff) -> list[dict]:
    """Return media_files rows where is_cleaned = false AND extracted_content IS NOT NULL and created before cutoff."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, extracted_content
            FROM   media_files
            WHERE  is_cleaned = false
              AND  extracted_content IS NOT NULL
              AND  created_at < %s
            ORDER BY created_at
            """,
            (cutoff,),
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


def _run_media_cleaning(conn, cutoff) -> None:
    """
    For each media_file where is_cleaned = false AND extracted_content IS NOT NULL:
    call clean_media_content() and write back cleaned_content + is_cleaned.
    """
    rows = _fetch_uncleaned_media(conn, cutoff)
    logger.info("Media cleaning: %d rows pending", len(rows))
    if not rows:
        return

    ok = fail = skipped = 0
    t0 = time.monotonic()

    for row in rows:
        media_id          = row["id"]
        extracted_content = row["extracted_content"] or ""

        try:
            cleaned = clean_media_content(extracted_content)
            if cleaned is None:
                logger.warning("  cleaning returned None for media_id=%s", media_id)
                skipped += 1
                continue

            _update_media_cleaned_content(conn, media_id, cleaned)
            logger.debug("  cleaned media_id=%s", media_id)
            ok += 1

        except Exception as e:
            logger.error("  FAILED media_id=%s: %s", media_id, e)
            fail += 1

    logger.info(
        "Media cleaning done: %d ok, %d skipped, %d failed (%.1fs)",
        ok, skipped, fail, time.monotonic() - t0,
    )


# ---------------------------------------------------------------------------
# Step 4 — Salience scoring
# ---------------------------------------------------------------------------

def _fetch_unscored_chunks(conn, cutoff) -> list[dict]:
    """Return cleaned chunks where salience has not yet been computed and created before cutoff."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT mc.id,
                   mc.content,
                   mc.metadata,
                   EXISTS(
                       SELECT 1 FROM media_files mf
                       WHERE  mf.memory_chunk_id = mc.id
                   ) AS has_media
            FROM   memory_chunks mc
            WHERE  mc.is_cleaned = true
              AND  mc.is_salience_computed = false
              AND  mc.created_at < %s
              AND  NOT EXISTS (
                       SELECT 1 FROM media_files mf
                       WHERE  mf.memory_chunk_id = mc.id
                         AND  mf.is_cleaned = false
                   )
            ORDER BY mc.created_at
            """,
            (cutoff,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        cur.close()


def _update_chunk_salience(conn, chunk_id: str, score: float) -> None:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE memory_chunks
            SET    initial_salience      = %s,
                   is_salience_computed  = true
            WHERE  id = %s
            """,
            (score, chunk_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _run_salience_scoring(conn, cutoff) -> None:
    """
    For each cleaned chunk where is_salience_computed = false:
    call compute_salience() and write back initial_salience + is_salience_computed.
    """
    rows = _fetch_unscored_chunks(conn, cutoff)
    logger.info("Salience scoring: %d rows pending", len(rows))
    if not rows:
        return

    ok = fail = skipped = 0
    t0 = time.monotonic()

    for row in rows:
        chunk_id  = row["id"]
        content   = row["content"] or ""
        metadata  = row["metadata"] or {}
        has_media = row["has_media"]

        try:
            score = compute_salience(content, metadata, has_media)
            if score is None:
                logger.warning("  salience returned None for chunk_id=%s", chunk_id)
                skipped += 1
                continue

            _update_chunk_salience(conn, chunk_id, score)
            logger.debug("  scored chunk_id=%s  salience=%.3f", chunk_id, score)
            ok += 1

        except Exception as e:
            logger.error("  FAILED chunk_id=%s: %s", chunk_id, e)
            fail += 1

    logger.info(
        "Salience scoring done: %d ok, %d skipped, %d failed (%.1fs)",
        ok, fail, skipped, time.monotonic() - t0,
    )
