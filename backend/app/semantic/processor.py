import json
import logging
import os
import time
from typing import Optional

from app.db.connection import get_connection, close_connection
from app.semantic.extractor import extract
from app.semantic.schemas import SemanticOutput
from app.semantic import db_writer

logger = logging.getLogger("echomind.semantic.processor")

FAILURE_LOG_PATH = "logs/semantic_failures.log"


def _log_failure(chunk_id: str, raw_output: Optional[str]) -> None:
    """Write failed LLM outputs to file for debugging."""
    try:
        os.makedirs(os.path.dirname(FAILURE_LOG_PATH), exist_ok=True)
        with open(FAILURE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n--- chunk_id={chunk_id} ---\n")
            f.write((raw_output or "NO OUTPUT") + "\n")
    except Exception as e:
        logger.error(f"Failed to write failure log: {e}")


def _fetch_eligible_chunks(conn) -> list[dict]:
    """
    Fetch memory_chunks with initial_salience >= 0.4 and is_processed = false.
    Include media_content if available.
    """
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT mc.id, mc.user_id, mc.content, mc.raw_content,
                   mc.timestamp, mc.participants, mc.initial_salience,
                   (
                       SELECT string_agg(mf.cleaned_content, ' ')
                       FROM media_files mf
                       WHERE mf.memory_chunk_id = mc.id
                         AND mf.cleaned_content IS NOT NULL
                         AND mf.cleaned_content <> ''
                   ) AS media_content

            FROM memory_chunks mc
            WHERE mc.initial_salience >= 0.4
              AND mc.is_processed = false
            ORDER BY mc.created_at
            """
        )

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    finally:
        cur.close()


def _mark_processed(conn, chunk_id: str) -> None:
    """Mark chunk as processed."""
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE memory_chunks SET is_processed = true WHERE id = %s",
            (chunk_id,),
        )
        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _build_semantic_input(row: dict) -> dict:
    """Build semantic input including media content."""
    text = row.get("content") or row.get("raw_content") or ""
    media_content = row.get("media_content")

    if media_content:
        text += "\n\n[ATTACHMENT]\n" + media_content

    participants_raw = row.get("participants") or []
    if isinstance(participants_raw, str):
        try:
            participants_raw = json.loads(participants_raw)
        except Exception:
            participants_raw = []

    participants = [p.strip().lower() for p in participants_raw if p]

    timestamp = row.get("timestamp")
    if timestamp:
        timestamp = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)

    return {
        "text": text,
        "participants": participants,
        "timestamp": timestamp,
    }


def _validate_and_normalize_output(raw_output: str) -> Optional[SemanticOutput]:
    """Validate and clean LLM JSON output."""
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}")
        return None

    valid_event_types = {"decision", "meeting", "task", "discussion", "milestone", "other"}
    valid_roles = {"participant", "subject", "organizer", "mentioned", "owner", "assignee", "reporter"}

    # Coerce or drop event before Pydantic sees it
    event = data.get("event")
    if not isinstance(event, dict):
        data.pop("event", None)
    else:
        et = event.get("event_type")
        if et is None or et not in valid_event_types:
            if et is not None:
                logger.debug(f"Coercing invalid event_type '{et}' -> 'other'")
                event["event_type"] = "other"
            else:
                data.pop("event", None)

    # Drop relationships with null/missing entity or invalid role
    if "relationships" in data:
        data["relationships"] = [
            r for r in data["relationships"]
            if isinstance(r, dict)
            and r.get("entity") is not None
            and r.get("role") in valid_roles
        ]

    try:
        output = SemanticOutput(**data)
    except Exception as e:
        logger.warning(f"Schema validation failed: {e}")
        return None

    # clamp salience
    output.refined_salience = max(0.0, min(1.0, output.refined_salience))

    # deduplicate entities
    if output.entities:
        seen = set()
        deduplicated = []
        for entity in output.entities:
            key = (entity.name.strip().lower(), entity.type)
            if key not in seen:
                seen.add(key)
                if entity.name.strip():
                    deduplicated.append(entity)
        output.entities = deduplicated

    return output


def run_semantic() -> None:
    """
    Semantic pipeline with retry + failure logging.
    """
    logger.info("=== Semantic layer started ===")

    conn = get_connection()

    try:
        rows = _fetch_eligible_chunks(conn)
        logger.info(f"Semantic extraction: {len(rows)} chunks eligible")

        if not rows:
            return

        ok = fail = skip = 0
        t0 = time.monotonic()

        for row in rows:
            chunk_id = row["id"]
            user_id = row["user_id"]
            initial_salience = row["initial_salience"]

            logger.debug(f"Processing chunk_id={chunk_id} salience={initial_salience:.3f}")

            try:
                semantic_input = _build_semantic_input(row)

                raw_output = extract(semantic_input)

                if not raw_output:
                    logger.warning(f"  extraction returned None for chunk_id={chunk_id}")
                    _log_failure(chunk_id, None)
                    skip += 1
                    _mark_processed(conn, chunk_id)
                    continue

                output = _validate_and_normalize_output(raw_output)

                if not output:
                    logger.info(f"  retrying extraction for chunk_id={chunk_id}")
                    raw_output_retry = extract(semantic_input)
                    if raw_output_retry:
                        output = _validate_and_normalize_output(raw_output_retry)
                        raw_output = raw_output_retry

                if not output:
                    logger.warning(f"  validation failed after retry for chunk_id={chunk_id}")
                    _log_failure(chunk_id, raw_output)
                    skip += 1
                    _mark_processed(conn, chunk_id)
                    continue

                db_writer.update_chunk_metadata(conn, chunk_id, output.refined_salience, output.event)

                entity_count = 0
                event_created = False

                if output.refined_salience >= 0.7:
                    entity_ids = db_writer.write_entities(
                        conn, user_id, output.entities, row["timestamp"]
                    )
                    entity_count = len(entity_ids)

                    if output.event:
                        event_id = db_writer.write_event(
                            conn, user_id, output.event, output.refined_salience
                        )

                        if event_id:
                            event_created = True
                            db_writer.write_relationships(
                                conn, entity_ids, event_id, output.relationships
                            )
                            db_writer.write_event_memory_link(conn, event_id, chunk_id)

                elif output.refined_salience >= 0.4:
                    entity_ids = db_writer.write_entities(
                        conn, user_id, output.entities, row["timestamp"]
                    )
                    entity_count = len(entity_ids)

                logger.info(
                    f"  chunk_id={chunk_id} entities={entity_count} "
                    f"event={'yes' if event_created else 'no'} salience={output.refined_salience:.3f}"
                )

                _mark_processed(conn, chunk_id)
                ok += 1

            except Exception as e:
                logger.error(f"  FAILED chunk_id={chunk_id}: {e}")
                fail += 1

                try:
                    _log_failure(chunk_id, None)
                    _mark_processed(conn, chunk_id)
                except Exception as e2:
                    logger.error(f"  Failed to mark chunk processed: {e2}")

        logger.info(
            f"Semantic extraction done: {ok} ok, {skip} skipped, {fail} failed ({time.monotonic() - t0:.1f}s)"
        )

    finally:
        close_connection(conn)

    logger.info("=== Semantic layer complete ===")