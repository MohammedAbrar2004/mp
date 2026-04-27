"""
Seed realistic synthetic data into ingestion_runs, system_logs, processing_queue.
Safe to run multiple times (uses ON CONFLICT DO NOTHING or checks before insert).
Run from backend/ with: python seed_pipeline_data.py
"""

import psycopg2
import json
from datetime import datetime, timezone, timedelta

DB = dict(dbname="mp", user="postgres", password="postgres123", host="localhost", port=5432)

# Chunk IDs that exist in memory_chunks but are not yet in processing_queue
CHUNK_IDS = [
    "33d90af3-2012-4e6e-80e6-0c95c0fc526f",
    "a72ae13c-9e92-4bab-b6cb-98ddd363db57",
    "1a69163a-8ab8-43e9-9a17-efac0a0df2f8",
    "294d212a-b580-4793-b1c4-93c9b90dabe9",
    "58a21428-ff89-409f-937c-a8e9fb4bf92e",
    "7eacf51b-f26f-43be-a1ce-97fbee51cda1",
    "a3a70ebb-6b6f-4203-b405-a22f5a462082",
    "cc6a0fc4-6086-4f57-823b-7b7d4fff546c",
    "3319dcd1-fb78-4813-87ef-1450c99834fb",
    "8b1d598c-01ad-4d99-a0ff-a0d1eb520729",
]

NOW = datetime.now(timezone.utc)


def ts(days_ago=0, hours_ago=0, minutes_ago=0):
    return NOW - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)


def seed_ingestion_runs(cur):
    rows = [
        # connector, timestamp, chunks, duration_ms, status
        ("gmail",    ts(0, 2),   14, 4210, "success"),
        ("gmail",    ts(1, 3),   22, 5830, "success"),
        ("gmail",    ts(2, 1),    0, 2100, "error"),
        ("gmail",    ts(3, 4),   18, 4650, "success"),
        ("gmail",    ts(5, 0),    9, 3200, "success"),
        ("calendar", ts(0, 4),    6, 1820, "success"),
        ("calendar", ts(1, 6),    4, 1540, "success"),
        ("calendar", ts(3, 2),    0, 1100, "error"),
        ("calendar", ts(6, 8),    8, 2010, "success"),
        ("whatsapp", ts(0, 1),   31, 720,  "success"),
        ("whatsapp", ts(0, 3),   47, 890,  "success"),
        ("whatsapp", ts(1, 0),   19, 510,  "success"),
        ("whatsapp", ts(2, 5),    0, 430,  "error"),
        ("manual",   ts(0, 0, 35), 1, 310, "success"),
        ("manual",   ts(1, 2),    2, 420,  "success"),
    ]
    for connector, timestamp, chunks, duration_ms, status in rows:
        cur.execute(
            """
            INSERT INTO ingestion_runs (connector, timestamp, chunks, duration_ms, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (connector, timestamp, chunks, duration_ms, status),
        )
    print(f"  ingestion_runs: {len(rows)} rows inserted")


def seed_system_logs(cur):
    rows = [
        # level, component, message, context, created_at
        ("info",    "gmail_connector",     "Gmail sync started",                                  None,                                              ts(0, 2, 5)),
        ("info",    "gmail_connector",     "Gmail sync completed: 14 new messages ingested",       json.dumps({"chunks": 14}),                        ts(0, 2)),
        ("info",    "gmail_connector",     "Gmail sync started",                                  None,                                              ts(1, 3, 5)),
        ("info",    "gmail_connector",     "Gmail sync completed: 22 new messages ingested",       json.dumps({"chunks": 22}),                        ts(1, 3)),
        ("error",   "gmail_connector",     "OAuth token expired, re-authentication required",      json.dumps({"error": "invalid_grant"}),            ts(2, 1)),
        ("info",    "calendar_connector",  "Calendar sync completed: 6 events processed",          json.dumps({"chunks": 6}),                         ts(0, 4)),
        ("warning", "calendar_connector",  "Calendar event missing start time, skipped",           json.dumps({"event_id": "evt_9xk2"}),              ts(1, 6, 10)),
        ("error",   "calendar_connector",  "Calendar sync failed: quota exceeded",                 json.dumps({"status": 429}),                       ts(3, 2)),
        ("info",    "whatsapp_bridge",     "WhatsApp bridge connected, listening for messages",    None,                                              ts(0, 0, 10)),
        ("info",    "whatsapp_bridge",     "31 new WhatsApp messages received and queued",         json.dumps({"chunks": 31}),                        ts(0, 1)),
        ("info",    "whatsapp_bridge",     "47 new WhatsApp messages received and queued",         json.dumps({"chunks": 47}),                        ts(0, 3)),
        ("error",   "whatsapp_bridge",     "WhatsApp session expired, QR scan required",           json.dumps({"session": "stale"}),                  ts(2, 5)),
        ("info",    "preprocessing",       "Preprocessing pipeline started: 8 chunks pending",     None,                                              ts(0, 1, 55)),
        ("info",    "preprocessing",       "Preprocessing complete: 8 cleaned, 0 failed",          json.dumps({"ok": 8, "fail": 0}),                  ts(0, 1, 40)),
        ("info",    "preprocessing",       "Salience scoring: 6 chunks scored",                    json.dumps({"scored": 6}),                         ts(0, 1, 35)),
        ("warning", "preprocessing",       "Media extraction returned None for audio chunk",        json.dumps({"chunk_id": "a72ae13c"}),              ts(1, 0, 20)),
        ("info",    "semantic_extractor",  "Semantic extraction started: 5 chunks eligible",       None,                                              ts(0, 1, 30)),
        ("info",    "semantic_extractor",  "Semantic extraction complete: 4 ok, 1 skipped",        json.dumps({"ok": 4, "skip": 1}),                  ts(0, 1, 15)),
        ("error",   "semantic_extractor",  "Ollama timeout after 120s on chunk a72ae13c",           json.dumps({"chunk_id": "a72ae13c", "attempt": 3}), ts(1, 2, 10)),
        ("warning", "semantic_extractor",  "Pydantic validation failed on LLM output, retrying",   json.dumps({"chunk_id": "1a69163a"}),              ts(2, 3, 5)),
    ]
    for level, component, message, context, created_at in rows:
        cur.execute(
            """
            INSERT INTO system_logs (level, component, message, context, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (level, component, message, context, created_at),
        )
    print(f"  system_logs: {len(rows)} rows inserted")


def seed_processing_queue(cur, chunk_ids):
    statuses = ["done", "done", "done", "done", "done", "done", "failed", "done", "retry", "done"]
    errors = [None, None, None, None, None, None, "Ollama timeout after 120s", None, "JSON parse failed on attempt 1", None]
    retries = [0, 0, 0, 0, 0, 0, 3, 0, 1, 0]

    inserted = 0
    for i, chunk_id in enumerate(chunk_ids[:len(statuses)]):
        # Guard: skip if already exists (UNIQUE on memory_chunk_id)
        cur.execute("SELECT 1 FROM processing_queue WHERE memory_chunk_id = %s", (chunk_id,))
        if cur.fetchone():
            continue
        status = statuses[i]
        last_error = errors[i]
        retry_count = retries[i]
        created_at = ts(0, i + 1)
        updated_at = ts(0, i)
        cur.execute(
            """
            INSERT INTO processing_queue
              (memory_chunk_id, status, retry_count, last_error, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (chunk_id, status, retry_count, last_error, created_at, updated_at),
        )
        inserted += 1
    print(f"  processing_queue: {inserted} rows inserted")


def main():
    conn = psycopg2.connect(**DB)
    try:
        with conn.cursor() as cur:
            print("Seeding pipeline data...")
            seed_ingestion_runs(cur)
            seed_system_logs(cur)
            seed_processing_queue(cur, CHUNK_IDS)
        conn.commit()
        print("Done.")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
