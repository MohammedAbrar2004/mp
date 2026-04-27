"""
Seed the semantic layer directly — no Ollama required.

Looks up memory_chunks by external_message_id, then writes hand-authored
entities, events, relationships, and chunk metadata exactly as the real
semantic pipeline would. Safe to re-run (idempotent).

Usage (from backend/):
    python seed_semantic_data.py
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seed_semantic")

from datetime import datetime, timezone
from typing import Optional

from app.db.connection import get_connection, close_connection
from app.semantic import db_writer
from app.semantic.processor import _mark_processed
from app.semantic.schemas import Entity, Event, Relationship


# ---------------------------------------------------------------------------
# Entity catalogue
# ---------------------------------------------------------------------------

ENTITIES = [
    Entity(name="Abrar",           type="person"),
    Entity(name="Amaan",           type="person"),
    Entity(name="Abdullah",        type="person"),
    Entity(name="Ma'am",           type="person"),
    Entity(name="Hadi",            type="person"),
    Entity(name="EchoMind",        type="project"),
    Entity(name="University",      type="organization"),
    Entity(name="WhatsApp",        type="tool"),
    Entity(name="Gmail",           type="tool"),
    Entity(name="Ollama",          type="tool"),
    Entity(name="GitHub",          type="tool"),
    Entity(name="pgvector",        type="technology"),
    Entity(name="PostgreSQL",      type="technology"),
    Entity(name="FastAPI",         type="technology"),
    Entity(name="Whisper",         type="technology"),
    Entity(name="Mistral",         type="technology"),
    Entity(name="lab",             type="location"),
    Entity(name="online",          type="location"),
    Entity(name="canteen",         type="location"),
    Entity(name="salience",        type="concept"),
    Entity(name="embedding",       type="concept"),
    Entity(name="preprocessing",   type="concept"),
    Entity(name="ingestion",       type="concept"),
    Entity(name="semantic-search", type="concept"),
    Entity(name="demo-prep",       type="task"),
    Entity(name="schema-migration",type="task"),
    Entity(name="search-ranking-fix", type="task"),
    Entity(name="authentication",  type="topic"),
    Entity(name="deployment",      type="topic"),
    Entity(name="testing",         type="topic"),
]

# Desired mention_count after seeding (drives salience_score via repeated mentions)
ENTITY_MENTION_COUNTS: dict[str, int] = {
    "abrar": 10, "amaan": 8, "abdullah": 8, "ma'am": 6, "hadi": 2,
    "echomind": 12, "university": 2,
    "whatsapp": 4, "gmail": 3, "ollama": 3, "github": 2,
    "pgvector": 4, "postgresql": 3, "fastapi": 2, "whisper": 3, "mistral": 3,
    "lab": 3, "online": 4, "canteen": 2,
    "salience": 4, "embedding": 4, "preprocessing": 5,
    "ingestion": 4, "semantic-search": 3,
    "demo-prep": 2, "schema-migration": 2, "search-ranking-fix": 2,
    "authentication": 2, "deployment": 2, "testing": 3,
}


# ---------------------------------------------------------------------------
# High-salience specs  (entities + event + relationships written)
# ---------------------------------------------------------------------------

def _d(day: int, hour: int, minute: int = 0) -> str:
    days = [20, 21, 22, 23, 24, 25, 26]
    dt = datetime(2026, 4, days[day - 1], hour, minute, tzinfo=timezone.utc)
    return dt.isoformat()


HIGH_SALIENCE: list[dict] = [
    {
        "external_id": "calendar_1",
        "refined_salience": 0.85,
        "title": "EchoMind Kickoff Meeting",
        "summary": "Architecture finalised, tasks divided, deadlines set",
        "keywords": ["kickoff", "architecture", "tasks"],
        "event": Event(
            title="EchoMind Kickoff Meeting",
            summary="Architecture finalised, tasks divided, deadlines set",
            event_type="meeting",
            timestamp=_d(1, 9),
            keywords=["kickoff", "architecture", "tasks"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="participant"),
            Relationship(entity="Amaan",    role="participant"),
            Relationship(entity="Abdullah", role="participant"),
            Relationship(entity="EchoMind", role="subject"),
        ],
    },
    {
        "external_id": "calendar_4",
        "refined_salience": 0.90,
        "title": "Mid-Project Review with Ma'am",
        "summary": "Demo walkthrough and architecture review with supervisor",
        "keywords": ["review", "demo", "supervisor"],
        "event": Event(
            title="Mid-Project Review with Ma'am",
            summary="Demo walkthrough and architecture review with supervisor",
            event_type="meeting",
            timestamp=_d(3, 11),
            keywords=["review", "demo", "supervisor"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="participant"),
            Relationship(entity="Amaan",    role="participant"),
            Relationship(entity="Abdullah", role="participant"),
            Relationship(entity="Ma'am",    role="organizer"),
        ],
    },
    {
        "external_id": "calendar_11",
        "refined_salience": 0.95,
        "title": "Final Submission Deadline",
        "summary": "Project repository and documentation submitted",
        "keywords": ["submission", "deadline", "repository"],
        "event": Event(
            title="Final Submission Deadline",
            summary="Project repository and documentation submitted",
            event_type="milestone",
            timestamp=_d(7, 9),
            keywords=["submission", "deadline", "repository"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="owner"),
            Relationship(entity="Amaan",    role="participant"),
            Relationship(entity="Abdullah", role="participant"),
            Relationship(entity="EchoMind", role="subject"),
        ],
    },
    {
        "external_id": "calendar_12",
        "refined_salience": 0.90,
        "title": "EchoMind Presentation",
        "summary": "Final presentation to Ma'am and evaluators in Lab 3",
        "keywords": ["presentation", "demo", "evaluation"],
        "event": Event(
            title="EchoMind Presentation",
            summary="Final presentation to Ma'am and evaluators in Lab 3",
            event_type="meeting",
            timestamp=_d(7, 10),
            keywords=["presentation", "demo", "evaluation"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="participant"),
            Relationship(entity="Amaan",    role="participant"),
            Relationship(entity="Abdullah", role="participant"),
            Relationship(entity="Ma'am",    role="organizer"),
            Relationship(entity="lab",      role="mentioned"),
        ],
    },
    {
        "external_id": "gmail_1",
        "refined_salience": 0.85,
        "title": "Task Assignment Email to Team",
        "summary": "Abrar assigned WhatsApp, Amaan Gmail, Abdullah semantic layer",
        "keywords": ["assignment", "tasks", "roles"],
        "event": Event(
            title="Task Assignment Email to Team",
            summary="Abrar assigned WhatsApp, Amaan Gmail, Abdullah semantic layer",
            event_type="task",
            timestamp=_d(1, 11),
            keywords=["assignment", "tasks", "roles"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="organizer"),
            Relationship(entity="Amaan",    role="assignee"),
            Relationship(entity="Abdullah", role="assignee"),
            Relationship(entity="EchoMind", role="subject"),
        ],
    },
    {
        "external_id": "gmail_4",
        "refined_salience": 0.80,
        "title": "Day 1 Progress Update to Ma'am",
        "summary": "Architecture finalised, connectors started, update sent",
        "keywords": ["progress", "update", "architecture"],
        "event": Event(
            title="Day 1 Progress Update to Ma'am",
            summary="Architecture finalised, connectors started, update sent",
            event_type="discussion",
            timestamp=_d(1, 18),
            keywords=["progress", "update", "architecture"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="reporter"),
            Relationship(entity="Ma'am",    role="mentioned"),
            Relationship(entity="EchoMind", role="subject"),
        ],
    },
    {
        "external_id": "gmail_9",
        "refined_salience": 0.85,
        "title": "Meeting Confirmation with Ma'am",
        "summary": "Meeting confirmed for Day 3 at 11 AM",
        "keywords": ["meeting", "confirmation", "schedule"],
        "event": Event(
            title="Meeting Confirmation with Ma'am",
            summary="Meeting confirmed for Day 3 at 11 AM",
            event_type="meeting",
            timestamp=_d(2, 20),
            keywords=["meeting", "confirmation", "schedule"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="organizer"),
            Relationship(entity="Ma'am",    role="participant"),
        ],
    },
    {
        "external_id": "gmail_11",
        "refined_salience": 0.85,
        "title": "Post-Meeting Summary Email",
        "summary": "Action items from Ma'am review distributed to team",
        "keywords": ["meeting", "action-items", "summary"],
        "event": Event(
            title="Post-Meeting Summary Email",
            summary="Action items from Ma'am review distributed to team",
            event_type="meeting",
            timestamp=_d(3, 13),
            keywords=["meeting", "action-items", "summary"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="organizer"),
            Relationship(entity="Amaan",    role="assignee"),
            Relationship(entity="Abdullah", role="assignee"),
            Relationship(entity="Ma'am",    role="mentioned"),
        ],
    },
    {
        "external_id": "gmail_24",
        "refined_salience": 0.90,
        "title": "EchoMind Submission Email Sent",
        "summary": "Repository link and README sent to Ma'am for submission",
        "keywords": ["submission", "email", "repository"],
        "event": Event(
            title="EchoMind Submission Email Sent",
            summary="Repository link and README sent to Ma'am for submission",
            event_type="milestone",
            timestamp=_d(7, 9),
            keywords=["submission", "email", "repository"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="owner"),
            Relationship(entity="Ma'am",    role="mentioned"),
            Relationship(entity="EchoMind", role="subject"),
        ],
    },
    {
        "external_id": "whatsapp_6",
        "refined_salience": 0.85,
        "title": "Team Task Split Decided",
        "summary": "Abrar WhatsApp, Amaan Gmail, Abdullah semantic and DB",
        "keywords": ["decision", "roles", "split"],
        "event": Event(
            title="Team Task Split Decided",
            summary="Abrar WhatsApp, Amaan Gmail, Abdullah semantic and DB",
            event_type="decision",
            timestamp=_d(1, 9, 25),
            keywords=["decision", "roles", "split"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="assignee"),
            Relationship(entity="Amaan",    role="assignee"),
            Relationship(entity="Abdullah", role="assignee"),
            Relationship(entity="EchoMind", role="subject"),
        ],
    },
    {
        "external_id": "whatsapp_20",
        "refined_salience": 0.85,
        "title": "Meeting Reminder with Demo Requirement",
        "summary": "Team reminded to have demo running before Ma'am meeting",
        "keywords": ["meeting", "demo", "reminder"],
        "event": Event(
            title="Meeting Reminder with Demo Requirement",
            summary="Team reminded to have demo running before Ma'am meeting",
            event_type="meeting",
            timestamp=_d(3, 10),
            keywords=["meeting", "demo", "reminder"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="organizer"),
            Relationship(entity="Amaan",    role="participant"),
            Relationship(entity="Abdullah", role="participant"),
            Relationship(entity="Ma'am",    role="mentioned"),
            Relationship(entity="demo-prep",role="subject"),
        ],
    },
    {
        "external_id": "whatsapp_35",
        "refined_salience": 0.85,
        "title": "Full Pipeline Run Complete",
        "summary": "All 100 chunks ingested after overnight processing run",
        "keywords": ["milestone", "ingestion", "pipeline"],
        "event": Event(
            title="Full Pipeline Run Complete",
            summary="All 100 chunks ingested after overnight processing run",
            event_type="milestone",
            timestamp=_d(6, 23),
            keywords=["milestone", "ingestion", "pipeline"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="reporter"),
            Relationship(entity="EchoMind", role="subject"),
            Relationship(entity="ingestion",role="mentioned"),
        ],
    },
    {
        "external_id": "manual_1",
        "refined_salience": 0.80,
        "title": "Architecture Finalised — Three Layers",
        "summary": "Ingestion, preprocessing, semantic layers confirmed and testable",
        "keywords": ["architecture", "decision", "layers"],
        "event": Event(
            title="Architecture Finalised — Three Layers",
            summary="Ingestion, preprocessing, semantic layers confirmed and testable",
            event_type="decision",
            timestamp=_d(1, 21),
            keywords=["architecture", "decision", "layers"],
        ),
        "relationships": [
            Relationship(entity="Abrar",         role="owner"),
            Relationship(entity="EchoMind",      role="subject"),
            Relationship(entity="preprocessing", role="mentioned"),
            Relationship(entity="ingestion",     role="mentioned"),
        ],
    },
    {
        "external_id": "manual_6",
        "refined_salience": 0.85,
        "title": "Post Ma'am Meeting Action Items",
        "summary": "Salience scores to be visible in demo, video backup needed",
        "keywords": ["meeting", "action-items", "salience"],
        "event": Event(
            title="Post Ma'am Meeting Action Items",
            summary="Salience scores to be visible in demo, video backup needed",
            event_type="meeting",
            timestamp=_d(3, 13),
            keywords=["meeting", "action-items", "salience"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="reporter"),
            Relationship(entity="Ma'am",    role="organizer"),
            Relationship(entity="Abdullah", role="assignee"),
            Relationship(entity="salience", role="subject"),
        ],
    },
    {
        "external_id": "manual_13",
        "refined_salience": 0.85,
        "title": "Demo Rehearsal Completed Successfully",
        "summary": "All ten queries returning results under two seconds",
        "keywords": ["demo", "rehearsal", "milestone"],
        "event": Event(
            title="Demo Rehearsal Completed Successfully",
            summary="All ten queries returning results under two seconds",
            event_type="milestone",
            timestamp=_d(6, 17),
            keywords=["demo", "rehearsal", "milestone"],
        ),
        "relationships": [
            Relationship(entity="Abrar",          role="reporter"),
            Relationship(entity="EchoMind",       role="subject"),
            Relationship(entity="semantic-search",role="mentioned"),
        ],
    },
    {
        "external_id": "manual_18",
        "refined_salience": 0.90,
        "title": "EchoMind Submission Done",
        "summary": "Repository submitted, presentation tomorrow at 10 AM",
        "keywords": ["submission", "milestone", "presentation"],
        "event": Event(
            title="EchoMind Submission Done",
            summary="Repository submitted, presentation tomorrow at 10 AM",
            event_type="milestone",
            timestamp=_d(7, 9, 15),
            keywords=["submission", "milestone", "presentation"],
        ),
        "relationships": [
            Relationship(entity="Abrar",    role="owner"),
            Relationship(entity="EchoMind", role="subject"),
        ],
    },
]


# ---------------------------------------------------------------------------
# Mid-salience specs  (refined_salience + entities only, no event)
# ---------------------------------------------------------------------------

MID_SALIENCE: list[dict] = [
    {"external_id": "whatsapp_1",  "refined_salience": 0.70,
     "entity_names": ["Abrar", "Amaan", "Abdullah", "EchoMind"]},
    {"external_id": "whatsapp_17", "refined_salience": 0.65,
     "entity_names": ["Amaan", "EchoMind", "search-ranking-fix"]},
    {"external_id": "whatsapp_23", "refined_salience": 0.65,
     "entity_names": ["Abrar", "Amaan", "Abdullah", "preprocessing"]},
    {"external_id": "whatsapp_31", "refined_salience": 0.70,
     "entity_names": ["Abrar", "WhatsApp"]},
    {"external_id": "gmail_5",     "refined_salience": 0.55,
     "entity_names": ["Ma'am", "Abrar", "EchoMind"]},
    {"external_id": "gmail_10",    "refined_salience": 0.60,
     "entity_names": ["Ma'am", "Abrar"]},
    {"external_id": "gmail_13",    "refined_salience": 0.65,
     "entity_names": ["Hadi", "Abrar", "EchoMind", "search-ranking-fix"]},
    {"external_id": "calendar_2",  "refined_salience": 0.75,
     "entity_names": ["Abrar", "Amaan", "WhatsApp", "Gmail"]},
    {"external_id": "calendar_5",  "refined_salience": 0.75,
     "entity_names": ["Amaan", "preprocessing"]},
    {"external_id": "calendar_7",  "refined_salience": 0.75,
     "entity_names": ["Abdullah", "embedding", "salience", "pgvector"]},
    {"external_id": "manual_7",    "refined_salience": 0.55,
     "entity_names": ["Abrar", "EchoMind", "deployment"]},
    {"external_id": "manual_10",   "refined_salience": 0.60,
     "entity_names": ["Abrar", "Ollama", "demo-prep"]},
    {"external_id": "manual_16",   "refined_salience": 0.55,
     "entity_names": ["Abrar", "preprocessing"]},
]


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _lookup_chunks(conn, external_ids: list[str]) -> dict[str, tuple[str, str]]:
    """Returns {external_id: (chunk_uuid, user_id)} for found chunks."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT external_message_id, id, user_id
            FROM memory_chunks
            WHERE external_message_id = ANY(%s)
              AND initial_salience >= 0.4
            """,
            (external_ids,),
        )
        result = {}
        for ext_id, chunk_id, user_id in cur.fetchall():
            result[ext_id] = (str(chunk_id), str(user_id))
        missing = set(external_ids) - set(result)
        for m in sorted(missing):
            logger.warning(f"  Not found or salience < 0.4: {m}")
        return result
    finally:
        cur.close()


def _get_user_id(conn) -> str:
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users LIMIT 1")
        row = cur.fetchone()
        if not row:
            raise RuntimeError("No users in DB — run seed_synthetic_data.py first")
        return str(row[0])
    finally:
        cur.close()


def _seed_entities(conn, user_id: str) -> dict[str, str]:
    """
    Upsert all entities, then set mention_count and salience_score directly.
    Returns {normalized_name: entity_id}.
    """
    # Initial upsert — one call, mention_count starts at 1 for each
    timestamp = datetime(2026, 4, 20, tzinfo=timezone.utc)
    entity_ids = db_writer.write_entities(conn, user_id, ENTITIES, timestamp)
    entity_map = {name: eid for eid, name in entity_ids}

    # Set desired mention_count and recalculate salience_score
    cur = conn.cursor()
    try:
        for normalized_name, count in ENTITY_MENTION_COUNTS.items():
            salience = min(1.0, 0.5 + (count - 1) * 0.05)
            cur.execute(
                """
                UPDATE entities
                SET mention_count = %s, salience_score = %s
                WHERE normalized_name = %s AND user_id = %s
                """,
                (count, salience, normalized_name, user_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    logger.info(f"Seeded {len(entity_ids)} entities")
    return entity_map


def _seed_high(conn, chunk_id: str, user_id: str, entity_map: dict[str, str],
               timestamp: Optional[str], spec: dict) -> None:
    event: Event = spec["event"]

    db_writer.update_chunk_metadata(conn, chunk_id, spec["refined_salience"], event)

    event_id = db_writer.write_event(conn, user_id, event, spec["refined_salience"])
    if event_id:
        # write_relationships expects List[Tuple[entity_id, normalized_name]]
        entity_id_name_pairs = [(eid, name) for name, eid in entity_map.items()]
        db_writer.write_relationships(conn, entity_id_name_pairs, event_id, spec["relationships"])
        db_writer.write_event_memory_link(conn, event_id, chunk_id)

    _mark_processed(conn, chunk_id)


def _seed_mid(conn, chunk_id: str, user_id: str, entity_map: dict[str, str],
              timestamp: Optional[str], spec: dict) -> None:
    db_writer.update_chunk_metadata(conn, chunk_id, spec["refined_salience"])

    entities_subset = [e for e in ENTITIES if e.name in spec["entity_names"]]
    if entities_subset:
        db_writer.write_entities(conn, user_id, entities_subset, timestamp or datetime.now(timezone.utc))

    _mark_processed(conn, chunk_id)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=== Seeding semantic layer ===")
    conn = get_connection()

    try:
        user_id = _get_user_id(conn)
        logger.info(f"User: {user_id}")

        # Gather all external_ids we care about
        all_ext_ids = [s["external_id"] for s in HIGH_SALIENCE + MID_SALIENCE]
        chunk_map = _lookup_chunks(conn, all_ext_ids)
        logger.info(f"Chunks found: {len(chunk_map)} / {len(all_ext_ids)}")

        # Seed entities first — needed for relationship linking
        entity_map = _seed_entities(conn, user_id)

        ok = skip = 0

        # High-salience chunks
        for spec in HIGH_SALIENCE:
            ext_id = spec["external_id"]
            if ext_id not in chunk_map:
                logger.warning(f"Skipping {ext_id} — not found")
                skip += 1
                continue
            chunk_id, _ = chunk_map[ext_id]
            timestamp = spec["event"].timestamp
            try:
                _seed_high(conn, chunk_id, user_id, entity_map, timestamp, spec)
                logger.info(f"  [high] {ext_id} salience={spec['refined_salience']} event={spec['event'].title!r}")
                ok += 1
            except Exception as e:
                logger.error(f"  FAILED {ext_id}: {e}")
                skip += 1

        # Mid-salience chunks
        for spec in MID_SALIENCE:
            ext_id = spec["external_id"]
            if ext_id not in chunk_map:
                logger.warning(f"Skipping {ext_id} — not found")
                skip += 1
                continue
            chunk_id, _ = chunk_map[ext_id]
            try:
                _seed_mid(conn, chunk_id, user_id, entity_map, None, spec)
                logger.info(f"  [mid]  {ext_id} salience={spec['refined_salience']}")
                ok += 1
            except Exception as e:
                logger.error(f"  FAILED {ext_id}: {e}")
                skip += 1

        logger.info(f"\nDone: {ok} seeded, {skip} skipped")
        logger.info("=== Semantic seed complete ===")

    finally:
        close_connection(conn)


if __name__ == "__main__":
    main()
