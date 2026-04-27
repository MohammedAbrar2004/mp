import asyncio
import os
import shutil
import time
from datetime import datetime, timezone

import psycopg2.extras
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.api.frontend_api.dependencies import get_db, USER_ID

router = APIRouter(prefix="/connectors", tags=["connectors"])

WHATSAPP_SESSION_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../../api/whatsapp/session"
)
WHATSAPP_SESSION_PATH = os.path.abspath(WHATSAPP_SESSION_PATH)

GMAIL_TOKEN_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../secrets/token.json"
)
GMAIL_TOKEN_PATH = os.path.abspath(GMAIL_TOKEN_PATH)

CALENDAR_TOKEN_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../secrets/token_calendar.json"
)
CALENDAR_TOKEN_PATH = os.path.abspath(CALENDAR_TOKEN_PATH)

EXCLUDED_CONNECTORS = {"gmeet"}


def _get_whatsapp_status() -> str:
    if not os.path.exists(WHATSAPP_SESSION_PATH):
        return "auth_required"
    files = os.listdir(WHATSAPP_SESSION_PATH)
    if not files:
        return "auth_required"
    return "active"


@router.get("/status")
def get_connector_status(conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT ds.id, ds.name, ds.is_active, ds.ingestion_mode,
                   ds.last_synced_at,
                   COUNT(mc.id) AS chunks_ingested
            FROM data_sources ds
            LEFT JOIN memory_chunks mc ON mc.source_id = ds.id
            GROUP BY ds.id
            ORDER BY ds.name
            """
        )
        rows = cur.fetchall()

    result = []
    for r in rows:
        name = r["name"]
        if name in EXCLUDED_CONNECTORS:
            continue

        if name == "whatsapp":
            status = _get_whatsapp_status()
        elif r["is_active"]:
            status = "active"
        else:
            status = "inactive"

        result.append({
            "connector": name,
            "name": name.title(),
            "is_active": r["is_active"],
            "last_synced_at": r["last_synced_at"].isoformat() if r["last_synced_at"] else None,
            "chunks_ingested": int(r["chunks_ingested"]),
            "mode": r["ingestion_mode"],
            "status": status,
        })

    return {"connectors": result}


@router.get("/runs")
def get_ingestion_runs(
    connector: str = Query(""),
    limit: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if connector:
            cur.execute(
                """
                SELECT id, connector, timestamp, chunks, duration_ms, status
                FROM ingestion_runs
                WHERE connector = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (connector, limit),
            )
        else:
            cur.execute(
                """
                SELECT id, connector, timestamp, chunks, duration_ms, status
                FROM ingestion_runs
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
        rows = cur.fetchall()

    return {
        "runs": [
            {
                "id": str(r["id"]),
                "connector": r["connector"],
                "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
                "chunks": r["chunks"],
                "duration_ms": r["duration_ms"],
                "status": r["status"],
            }
            for r in rows
        ]
    }


@router.get("/logs")
def get_connector_logs(
    connector: str = Query(""),
    limit: int = Query(50, ge=1, le=200),
    conn=Depends(get_db),
):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if connector:
            cur.execute(
                """
                SELECT level, component, message, created_at
                FROM system_logs
                WHERE component ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (f"%{connector}%", limit),
            )
        else:
            cur.execute(
                """
                SELECT level, component, message, created_at
                FROM system_logs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
        rows = cur.fetchall()

    return {
        "logs": [
            {
                "level": r["level"],
                "component": r["component"],
                "message": r["message"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
    }


def _record_run_start(connector_name: str) -> str:
    from app.db.connection import get_connection, close_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_runs (connector, status)
                VALUES (%s, 'running')
                RETURNING id
                """,
                (connector_name,),
            )
            run_id = str(cur.fetchone()[0])
            conn.commit()
        return run_id
    finally:
        close_connection(conn)


def _record_run_end(run_id: str, chunks: int, duration_ms: int, status: str):
    from app.db.connection import get_connection, close_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingestion_runs
                SET chunks = %s, duration_ms = %s, status = %s
                WHERE id = %s
                """,
                (chunks, duration_ms, status, run_id),
            )
            conn.commit()
    finally:
        close_connection(conn)


def _count_recent_chunks(connector_name: str) -> int:
    from app.db.connection import get_connection, close_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM memory_chunks mc
                JOIN data_sources ds ON ds.id = mc.source_id
                WHERE ds.name = %s AND mc.created_at > NOW() - INTERVAL '10 minutes'
                """,
                (connector_name,),
            )
            return cur.fetchone()[0]
    finally:
        close_connection(conn)


async def _run_gmail_sync(run_id: str):
    t0 = time.monotonic()
    status = "success"
    try:
        from app.connectors.gmail.run_gmail_ingestion import run
        await asyncio.to_thread(run)
    except Exception as e:
        status = "error"
        from app.db.connection import get_connection, close_connection
        import logging
        logging.getLogger("echomind").error("Gmail sync failed: %s", str(e))
    finally:
        duration_ms = int((time.monotonic() - t0) * 1000)
        chunks = _count_recent_chunks("gmail")
        _record_run_end(run_id, chunks, duration_ms, status)


async def _run_calendar_sync(run_id: str):
    t0 = time.monotonic()
    status = "success"
    try:
        from app.connectors.calendar.run_calendar_ingestion import run
        await asyncio.to_thread(run)
    except Exception as e:
        status = "error"
        import logging
        logging.getLogger("echomind").error("Calendar sync failed: %s", str(e))
    finally:
        duration_ms = int((time.monotonic() - t0) * 1000)
        chunks = _count_recent_chunks("calendar")
        _record_run_end(run_id, chunks, duration_ms, status)


@router.post("/{connector}/sync")
async def sync_connector(connector: str, background_tasks: BackgroundTasks):
    if connector == "whatsapp":
        return {"status": "push-only", "message": "WhatsApp is push-mode. Ensure the Node.js bridge is running."}
    if connector == "manual":
        return {"status": "no-op", "message": "Manual connector has no scheduled sync."}
    if connector == "gmail":
        run_id = _record_run_start("gmail")
        background_tasks.add_task(_run_gmail_sync, run_id)
        return {"status": "started", "connector": "gmail"}
    if connector == "calendar":
        run_id = _record_run_start("calendar")
        background_tasks.add_task(_run_calendar_sync, run_id)
        return {"status": "started", "connector": "calendar"}
    raise HTTPException(status_code=404, detail=f"Unknown connector: {connector}")


class PauseBody(BaseModel):
    is_active: bool


@router.patch("/{connector}/pause")
def pause_connector(connector: str, body: PauseBody, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE data_sources SET is_active = %s WHERE name = %s RETURNING id",
            (body.is_active, connector),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Connector '{connector}' not found")
        conn.commit()
    return {"status": "ok", "connector": connector, "is_active": body.is_active}


@router.post("/whatsapp/reauth")
def whatsapp_reauth():
    try:
        if os.path.exists(WHATSAPP_SESSION_PATH):
            shutil.rmtree(WHATSAPP_SESSION_PATH)
        os.makedirs(WHATSAPP_SESSION_PATH, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")
    return {"requires_qr": True}


@router.delete("/gmail/token")
def delete_gmail_token():
    if os.path.exists(GMAIL_TOKEN_PATH):
        os.remove(GMAIL_TOKEN_PATH)
    return {"requires_oauth": True}


@router.delete("/calendar/token")
def delete_calendar_token():
    if os.path.exists(CALENDAR_TOKEN_PATH):
        os.remove(CALENDAR_TOKEN_PATH)
    return {"requires_oauth": True}
