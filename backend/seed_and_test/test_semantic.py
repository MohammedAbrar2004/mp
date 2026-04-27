"""
Quick test: pick 10 random unprocessed chunks and run semantic extraction on them.
Resets is_processed=false after each run so you can re-test.

Usage:
    python test_semantic.py
    python test_semantic.py --reset    # mark all 10 chunks unprocessed again
"""

import argparse
import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)

from app.db.connection import get_connection, close_connection
from app.semantic.extractor import extract
from app.semantic.processor import (
    _build_semantic_input,
    _validate_and_normalize_output,
    _mark_processed,
    _log_failure,
)
from app.semantic import db_writer

logger = logging.getLogger("test_semantic")

SAMPLE_SIZE = 5


def fetch_sample(conn) -> list[dict]:
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
            ORDER BY random()
            LIMIT %s
            """,
            (SAMPLE_SIZE,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        cur.close()


def reset_chunks(conn, chunk_ids: list[str]) -> None:
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE memory_chunks SET is_processed = false WHERE id = ANY(%s::uuid[])",
            (chunk_ids,),
        )
        conn.commit()
        logger.info(f"Reset {cur.rowcount} chunks to is_processed=false")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def run_test(reset_after: bool = False) -> None:
    conn = get_connection()
    try:
        rows = fetch_sample(conn)
        logger.info(f"Sampled {len(rows)} chunks")

        if not rows:
            logger.warning("No eligible chunks found (initial_salience >= 0.4).")
            return

        chunk_ids = [r["id"] for r in rows]
        ok = fail = skip = 0

        for row in rows:
            chunk_id = row["id"]
            user_id = row["user_id"]
            salience = row["initial_salience"]

            preview = (row.get("content") or row.get("raw_content") or "")[:80].replace("\n", " ")
            logger.info(f"\n{'='*60}")
            logger.info(f"chunk_id={chunk_id}  salience={salience:.3f}")
            logger.info(f"preview : {preview!r}")

            try:
                semantic_input = _build_semantic_input(row)
                raw_output = extract(semantic_input)

                if not raw_output:
                    logger.warning("  -> extraction returned None")
                    _log_failure(chunk_id, None)
                    skip += 1
                    _mark_processed(conn, chunk_id)
                    continue

                output = _validate_and_normalize_output(raw_output)

                if not output:
                    logger.info("  -> validation failed, retrying once")
                    raw_output = extract(semantic_input)
                    if raw_output:
                        output = _validate_and_normalize_output(raw_output)

                if not output:
                    logger.warning("  -> validation failed after retry")
                    _log_failure(chunk_id, raw_output)
                    skip += 1
                    _mark_processed(conn, chunk_id)
                    continue

                logger.info(f"  salience : {salience:.3f} -> {output.refined_salience:.3f}")
                logger.info(f"  entities : {[f'{e.name} ({e.type})' for e in output.entities]}")
                if output.event:
                    logger.info(f"  event    : [{output.event.event_type}] {output.event.title!r}")
                    logger.info(f"  keywords : {output.event.keywords}")
                else:
                    logger.info("  event    : none")
                logger.info(f"  rels     : {[(r.entity, r.role) for r in output.relationships]}")

                db_writer.update_chunk_metadata(conn, chunk_id, output.refined_salience, output.event)

                if output.refined_salience >= 0.7:
                    entity_ids = db_writer.write_entities(conn, user_id, output.entities, row["timestamp"])
                    if output.event:
                        event_id = db_writer.write_event(conn, user_id, output.event, output.refined_salience)
                        if event_id:
                            db_writer.write_relationships(conn, entity_ids, event_id, output.relationships)
                            db_writer.write_event_memory_link(conn, event_id, chunk_id)
                elif output.refined_salience >= 0.4:
                    db_writer.write_entities(conn, user_id, output.entities, row["timestamp"])

                _mark_processed(conn, chunk_id)
                ok += 1

            except Exception as e:
                logger.error(f"  FAILED: {e}")
                fail += 1
                try:
                    _log_failure(chunk_id, None)
                    _mark_processed(conn, chunk_id)
                except Exception:
                    pass

        logger.info(f"\n{'='*60}")
        logger.info(f"DONE: {ok} ok  {skip} skipped  {fail} failed  (out of {len(rows)})")

        if reset_after:
            reset_chunks(conn, chunk_ids)

    finally:
        close_connection(conn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset", action="store_true",
        help="Mark the 10 sampled chunks as unprocessed after the run (for re-testing)"
    )
    args = parser.parse_args()
    run_test(reset_after=args.reset)
