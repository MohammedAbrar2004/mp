import os
import tempfile
import time
import json
import psycopg2.extras
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException

from pydantic import BaseModel

from app.api.frontend_api.dependencies import get_db, USER_ID
from app.retrieval.rag_engine import query_pipeline

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str


@router.post("")
def submit_query(body: QueryRequest, conn=Depends(get_db)):
    t0 = time.monotonic()
    answer, source_ids = query_pipeline(body.query, conn, user_id=USER_ID)
    response_time_ms = int((time.monotonic() - t0) * 1000)

    sources = []
    if source_ids:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT mc.id AS memory_chunk_id, mc.title, mc.summary,
                       mc.content_type, mc.refined_salience, mc.timestamp,
                       ds.name AS connector_source
                FROM memory_chunks mc
                JOIN data_sources ds ON ds.id = mc.source_id
                WHERE mc.id = ANY(%s::uuid[])
                """,
                (source_ids,),
            )
            rows = cur.fetchall()
            for r in rows:
                sources.append({
                    "memory_chunk_id": str(r["memory_chunk_id"]),
                    "title": r["title"],
                    "summary": r["summary"],
                    "content_type": r["content_type"],
                    "refined_salience": r["refined_salience"],
                    "connector_source": r["connector_source"],
                    "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
                })

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO user_queries (user_id, query, answer, response_time_ms, sources)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (USER_ID, body.query, answer, response_time_ms, json.dumps(sources)),
        )
        row = cur.fetchone()
        conn.commit()

    return {
        "query_id": str(row["id"]),
        "query": body.query,
        "answer": answer,
        "response_time_ms": response_time_ms,
        "sources": sources,
        "created_at": row["created_at"].isoformat(),
    }


@router.post("/voice")
async def voice_query(file: UploadFile = File(...), conn=Depends(get_db)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio file")

    suffix = ".webm"
    mime = file.content_type or "audio/webm"
    if "ogg" in mime:
        suffix = ".ogg"
    elif "mp4" in mime or "m4a" in mime:
        suffix = ".mp4"
    elif "wav" in mime:
        suffix = ".wav"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name

    try:
        from app.preprocessing.services.media.audio_processor import transcribe_audio
        transcript = transcribe_audio(tmp_path, mime)
    finally:
        os.unlink(tmp_path)

    if not transcript:
        raise HTTPException(status_code=422, detail="Could not transcribe audio")

    t0 = time.monotonic()
    answer, source_ids = query_pipeline(transcript, conn, user_id=USER_ID)
    response_time_ms = int((time.monotonic() - t0) * 1000)

    sources = []
    if source_ids:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT mc.id AS memory_chunk_id, mc.title, mc.summary,
                       mc.content_type, mc.refined_salience, mc.timestamp,
                       ds.name AS connector_source
                FROM memory_chunks mc
                JOIN data_sources ds ON ds.id = mc.source_id
                WHERE mc.id = ANY(%s::uuid[])
                """,
                (source_ids,),
            )
            for r in cur.fetchall():
                sources.append({
                    "memory_chunk_id": str(r["memory_chunk_id"]),
                    "title": r["title"],
                    "summary": r["summary"],
                    "content_type": r["content_type"],
                    "refined_salience": r["refined_salience"],
                    "connector_source": r["connector_source"],
                    "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
                })

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO user_queries (user_id, query, answer, response_time_ms, sources)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (USER_ID, transcript, answer, response_time_ms, json.dumps(sources)),
        )
        row = cur.fetchone()
        conn.commit()

    return {
        "query_id": str(row["id"]),
        "query": transcript,
        "answer": answer,
        "response_time_ms": response_time_ms,
        "sources": sources,
        "created_at": row["created_at"].isoformat(),
    }


@router.get("/history")
def get_query_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn=Depends(get_db),
):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, query, answer, response_time_ms, sources, created_at
            FROM user_queries
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (USER_ID, limit, offset),
        )
        rows = cur.fetchall()

        cur.execute(
            "SELECT COUNT(*) FROM user_queries WHERE user_id = %s", (USER_ID,)
        )
        total = cur.fetchone()["count"]

    queries = []
    for r in rows:
        queries.append({
            "query_id": str(r["id"]),
            "query": r["query"],
            "answer": r["answer"],
            "response_time_ms": r["response_time_ms"],
            "sources": r["sources"] if r["sources"] else [],
            "created_at": r["created_at"].isoformat(),
        })

    return {"queries": queries, "total": total}


@router.get("/sync-status")
def get_sync_status(conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT name, last_synced_at FROM data_sources")
        sources = cur.fetchall()

        cur.execute(
            """
            SELECT COUNT(*) FROM system_logs
            WHERE level = 'error'
              AND created_at > NOW() - INTERVAL '24 hours'
            """
        )
        failed_count = cur.fetchone()["count"]

    sync_map = {}
    for s in sources:
        sync_map[s["name"]] = s["last_synced_at"].isoformat() if s["last_synced_at"] else None

    return {
        "last_sync_per_source": sync_map,
        "failed_jobs_count": int(failed_count),
    }
