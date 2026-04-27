import psycopg2.extras
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from app.api.frontend_api.dependencies import get_db, USER_ID

router = APIRouter(prefix="/relations", tags=["relations"])

MAX_GRAPH_NODES = 60

VALID_TYPES = {"person", "project", "organization", "tool", "technology", "topic", "task", "location", "file", "concept"}


@router.get("/entities")
def get_relation_entities(conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, name, entity_type, mention_count, salience_score,
                   about, created_at AS first_seen, last_seen
            FROM entities
            WHERE user_id = %s AND mention_count > 7
            ORDER BY mention_count DESC
            LIMIT %s
            """,
            (USER_ID, MAX_GRAPH_NODES),
        )
        rows = cur.fetchall()

    return {
        "entities": [
            {
                "entity_id": str(r["id"]),
                "name": r["name"],
                "entity_type": r["entity_type"],
                "mention_count": r["mention_count"],
                "salience_score": r["salience_score"],
                "about": r["about"],
                "first_seen": r["first_seen"].isoformat() if r["first_seen"] else None,
                "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None,
            }
            for r in rows
        ]
    }


@router.get("/graph")
def get_relation_graph(
    entity_id: str = Query(""),
    min_shared_events: int = Query(1, ge=1, le=10),
    type_filter: str = Query("all"),
    conn=Depends(get_db),
):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if type_filter == "all" or type_filter not in VALID_TYPES:
            cur.execute(
                """
                SELECT id, name, entity_type, mention_count, about
                FROM entities
                WHERE user_id = %s AND mention_count > 7
                ORDER BY mention_count DESC
                LIMIT %s
                """,
                (USER_ID, MAX_GRAPH_NODES),
            )
        else:
            cur.execute(
                """
                SELECT id, name, entity_type, mention_count, about
                FROM entities
                WHERE user_id = %s AND mention_count > 7 AND entity_type = %s
                ORDER BY mention_count DESC
                LIMIT %s
                """,
                (USER_ID, type_filter, MAX_GRAPH_NODES),
            )
        all_entities = cur.fetchall()

    if not all_entities:
        return {"nodes": [], "edges": []}

    entity_map = {str(r["id"]): r for r in all_entities}
    entity_ids = list(entity_map.keys())

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                eel1.entity_id::text AS src,
                eel2.entity_id::text AS tgt,
                COUNT(DISTINCT eel1.event_id) AS shared_count,
                AVG(e.salience_score) AS avg_salience,
                (
                    SELECT ev2.title
                    FROM entity_event_links x1
                    JOIN entity_event_links x2 ON x1.event_id = x2.event_id
                    JOIN events ev2 ON ev2.id = x1.event_id
                    WHERE x1.entity_id = eel1.entity_id
                      AND x2.entity_id = eel2.entity_id
                    ORDER BY ev2.salience_score DESC
                    LIMIT 1
                ) AS top_event_title
            FROM entity_event_links eel1
            JOIN entity_event_links eel2
              ON eel1.event_id = eel2.event_id
             AND eel1.entity_id < eel2.entity_id
            JOIN events e ON e.id = eel1.event_id
            WHERE e.user_id = %s
              AND eel1.entity_id = ANY(%s::uuid[])
              AND eel2.entity_id = ANY(%s::uuid[])
            GROUP BY eel1.entity_id, eel2.entity_id
            HAVING COUNT(DISTINCT eel1.event_id) >= %s
            """,
            (USER_ID, entity_ids, entity_ids, min_shared_events),
        )
        raw_edges = cur.fetchall()

    edges = []
    connected_ids = set()

    for row in raw_edges:
        src, tgt = row["src"], row["tgt"]
        shared = int(row["shared_count"])
        weight = min(1.0, round(float(row["avg_salience"] or 0.5), 3))
        label = row["top_event_title"] or f"{shared} shared event{'s' if shared != 1 else ''}"

        if src not in entity_map or tgt not in entity_map:
            continue

        edges.append({
            "source_entity_id": src,
            "target_entity_id": tgt,
            "label": label,
            "weight": weight,
            "shared_event_count": shared,
        })
        connected_ids.add(src)
        connected_ids.add(tgt)

    # Ego-graph mode: filter to ego node + direct neighbors only
    if entity_id and entity_id in entity_map:
        ego_neighbors = {entity_id}
        for e in edges:
            if e["source_entity_id"] == entity_id:
                ego_neighbors.add(e["target_entity_id"])
            elif e["target_entity_id"] == entity_id:
                ego_neighbors.add(e["source_entity_id"])
        edges = [
            e for e in edges
            if e["source_entity_id"] in ego_neighbors and e["target_entity_id"] in ego_neighbors
        ]
        connected_ids = ego_neighbors

    nodes = [
        {
            "entity_id": str(r["id"]),
            "name": r["name"],
            "entity_type": r["entity_type"],
            "mention_count": r["mention_count"],
            "about": r["about"],
        }
        for r in all_entities
        if str(r["id"]) in connected_ids
    ]

    return {"nodes": nodes, "edges": edges}


class AboutBody(BaseModel):
    about: str = Field("", max_length=120)


@router.put("/entities/{entity_id}/about")
def update_entity_about(entity_id: str, body: AboutBody, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE entities SET about = %s WHERE id = %s AND user_id = %s RETURNING id",
            (body.about.strip() or None, entity_id, USER_ID),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entity not found")
        conn.commit()
    return {"entity_id": entity_id, "about": body.about.strip() or None}
