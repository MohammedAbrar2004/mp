import logging
from typing import List, Tuple, Optional
from datetime import datetime

from app.semantic.schemas import Entity, Event, Relationship

logger = logging.getLogger("echomind.semantic.db_writer")


def write_entities(
    conn,
    user_id: str,
    entities: List[Entity],
    timestamp: datetime,
) -> List[Tuple[str, str]]:
    """
    Upsert entities. On conflict, increment mention_count and bump salience_score by 0.05 (capped at 1.0).
    Returns list of (entity_id, normalized_name) for relationship linking.
    """
    if not entities:
        return []

    entity_ids_with_names = []
    cur = conn.cursor()

    try:
        for entity in entities:
            normalized_name = entity.name.strip().lower()

            cur.execute(
                """
                INSERT INTO entities (user_id, name, normalized_name, entity_type, mention_count, last_seen)
                VALUES (%s, %s, %s, %s, 1, %s)
                ON CONFLICT (normalized_name, entity_type, user_id)
                DO UPDATE SET
                    mention_count = entities.mention_count + 1,
                    last_seen = EXCLUDED.last_seen,
                    salience_score = LEAST(1.0, entities.salience_score + 0.05)
                RETURNING id
                """,
                (user_id, entity.name, normalized_name, entity.type, timestamp),
            )

            result = cur.fetchone()
            if result:
                entity_ids_with_names.append((result[0], normalized_name))

        conn.commit()
        logger.debug(f"Wrote {len(entity_ids_with_names)} entities")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to write entities: {e}")
        raise
    finally:
        cur.close()

    return entity_ids_with_names


def write_event(
    conn,
    user_id: str,
    event: Event,
    salience: float,
) -> Optional[str]:
    """Insert event. Returns event_id."""
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO events (user_id, title, summary, event_type, start_time, salience_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, event.title, event.summary, event.event_type, event.timestamp, salience),
        )

        result = cur.fetchone()
        conn.commit()

        if result:
            event_id = result[0]
            logger.debug(f"Wrote event: {event.title} (id={event_id})")
            return event_id

        return None

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to write event: {e}")
        raise
    finally:
        cur.close()


def write_relationships(
    conn,
    entity_ids_with_names: List[Tuple[str, str]],
    event_id: str,
    relationships: List[Relationship],
) -> None:
    """Link entities to event via entity_event_links."""
    if not entity_ids_with_names or not relationships:
        return

    entity_map = {name: eid for eid, name in entity_ids_with_names}
    cur = conn.cursor()

    try:
        for rel in relationships:
            normalized = rel.entity.strip().lower()
            if normalized not in entity_map:
                logger.debug(f"Relationship entity '{rel.entity}' not in extracted entities — skipping")
                continue

            cur.execute(
                """
                INSERT INTO entity_event_links (entity_id, event_id, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (entity_id, event_id, role) DO NOTHING
                """,
                (entity_map[normalized], event_id, rel.role),
            )

        conn.commit()
        logger.debug(f"Wrote {len(relationships)} relationships")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to write relationships: {e}")
        raise
    finally:
        cur.close()


def write_event_memory_link(conn, event_id: str, chunk_id: str) -> None:
    """Link event to source memory chunk."""
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO event_memory_links (event_id, memory_chunk_id)
            VALUES (%s, %s)
            ON CONFLICT (event_id, memory_chunk_id) DO NOTHING
            """,
            (event_id, chunk_id),
        )
        conn.commit()
        logger.debug(f"Wrote event_memory_link: event={event_id} chunk={chunk_id}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to write event_memory_link: {e}")
        raise
    finally:
        cur.close()


def update_chunk_metadata(
    conn,
    chunk_id: str,
    salience: float,
    event: Optional[Event] = None,
) -> None:
    """
    Write refined_salience back to memory_chunks.
    If an event is present, also write title, summary, and keywords.
    """
    cur = conn.cursor()

    try:
        if event:
            cur.execute(
                """
                UPDATE memory_chunks
                SET refined_salience = %s, title = %s, summary = %s, keywords = %s
                WHERE id = %s
                """,
                (salience, event.title, event.summary, event.keywords or [], chunk_id),
            )
        else:
            cur.execute(
                "UPDATE memory_chunks SET refined_salience = %s WHERE id = %s",
                (salience, chunk_id),
            )

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update chunk metadata: {e}")
        raise
    finally:
        cur.close()
