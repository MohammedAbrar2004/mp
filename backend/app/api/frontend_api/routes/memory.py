import psycopg2.extras
from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.frontend_api.dependencies import get_db, USER_ID

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/chunks")
def list_memory_chunks(
    search: str = Query(""),
    connector_source: str = Query(""),
    salience_min: float = Query(0.0, ge=0.0, le=1.0),
    salience_max: float = Query(1.0, ge=0.0, le=1.0),
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    per_page: int = Query(6, ge=1, le=50),
    conn=Depends(get_db),
):
    order_clause = {
        "newest": "mc.created_at DESC",
        "oldest": "mc.created_at ASC",
        "salience": "mc.refined_salience DESC NULLS LAST",
    }.get(sort, "mc.created_at DESC")

    offset = (page - 1) * per_page

    base_where = """
        mc.user_id = %(user_id)s
        AND mc.is_deleted = FALSE
        AND (%(search)s = '' OR mc.summary ILIKE '%%' || %(search)s || '%%'
             OR EXISTS (
                 SELECT 1 FROM unnest(mc.keywords) kw
                 WHERE kw ILIKE '%%' || %(search)s || '%%'
             ))
        AND (%(connector_source)s = '' OR ds.name = %(connector_source)s)
        AND COALESCE(mc.refined_salience, 0) BETWEEN %(salience_min)s AND %(salience_max)s
    """

    params = {
        "user_id": USER_ID,
        "search": search,
        "connector_source": connector_source,
        "salience_min": salience_min,
        "salience_max": salience_max,
        "per_page": per_page,
        "offset": offset,
    }

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            f"""
            SELECT COUNT(*)
            FROM memory_chunks mc
            JOIN data_sources ds ON ds.id = mc.source_id
            WHERE {base_where}
              AND EXISTS (
                SELECT 1 FROM event_memory_links eml WHERE eml.memory_chunk_id = mc.id
              )
            """,
            params,
        )
        total = cur.fetchone()["count"]

        cur.execute(
            f"""
            SELECT
                mc.id AS memory_chunk_id,
                mc.title,
                mc.summary,
                mc.keywords,
                mc.refined_salience,
                mc.content_type,
                mc.timestamp,
                mc.created_at,
                ds.name AS connector_source
            FROM memory_chunks mc
            JOIN data_sources ds ON ds.id = mc.source_id
            WHERE {base_where}
              AND EXISTS (
                SELECT 1 FROM event_memory_links eml WHERE eml.memory_chunk_id = mc.id
              )
            ORDER BY {order_clause}
            LIMIT %(per_page)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cur.fetchall()

    chunks = []
    for r in rows:
        chunks.append({
            "memory_chunk_id": str(r["memory_chunk_id"]),
            "title": r["title"],
            "summary": r["summary"],
            "keywords": r["keywords"] or [],
            "refined_salience": r["refined_salience"],
            "content_type": r["content_type"],
            "connector_source": r["connector_source"],
            "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        })

    return {"chunks": chunks, "total": int(total), "page": page, "per_page": per_page}


@router.get("/chunks/{chunk_id}")
def get_chunk_detail(chunk_id: str, conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT mc.id AS memory_chunk_id, mc.title, mc.summary, mc.raw_content,
                   mc.keywords, mc.content_type, mc.refined_salience,
                   mc.timestamp, mc.created_at, ds.name AS connector_source
            FROM memory_chunks mc
            JOIN data_sources ds ON ds.id = mc.source_id
            WHERE mc.id = %s AND mc.user_id = %s AND mc.is_deleted = FALSE
            """,
            (chunk_id, USER_ID),
        )
        chunk = cur.fetchone()
        if not chunk:
            raise HTTPException(status_code=404, detail="Memory chunk not found")

        cur.execute(
            """
            SELECT DISTINCT e.name, e.entity_type
            FROM event_memory_links eml
            JOIN entity_event_links eel ON eel.event_id = eml.event_id
            JOIN entities e ON e.id = eel.entity_id
            WHERE eml.memory_chunk_id = %s
            ORDER BY e.name
            """,
            (chunk_id,),
        )
        entities = cur.fetchall()

    return {
        "memory_chunk_id": str(chunk["memory_chunk_id"]),
        "title": chunk["title"],
        "summary": chunk["summary"],
        "raw_content": chunk["raw_content"],
        "keywords": chunk["keywords"] or [],
        "content_type": chunk["content_type"],
        "refined_salience": chunk["refined_salience"],
        "connector_source": chunk["connector_source"],
        "timestamp": chunk["timestamp"].isoformat() if chunk["timestamp"] else None,
        "created_at": chunk["created_at"].isoformat() if chunk["created_at"] else None,
        "entities": [{"name": e["name"], "entity_type": e["entity_type"]} for e in entities],
    }
