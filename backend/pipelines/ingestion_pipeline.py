from __future__ import annotations

from typing import List

from models.normalized_input import NormalizedInput
from app.services.media_service import MediaService
from app.db.connection import get_connection
from app.db.repository import insert_memory_chunk, insert_media_file


# TODO: Replace this with DB lookup from data_sources table
_SOURCE_ID_MAP: dict[str, str] = {
    "whatsapp": "39218ef4-b3ce-4b98-b1e2-34afa243c785",
    "gmail": "250f8201-6caa-4b88-8983-b450f8343af6",
    "gmeet": "1c03923e-730c-471b-95a0-4014d000414a",
    "calendar": "a26589c9-8edf-4f44-b7ec-ee5d9e06482e",
    "manual": "2f269226-cc45-4eb8-9c67-7efa8ecb3463",
}

# Single-user prototype: fixed user UUID
_USER_ID = "5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9"


def process(inputs: List[NormalizedInput]) -> None:
    """
    Process a list of NormalizedInput objects from any connector.

    For each input:
      1. Save any pending media to disk via MediaService.
      2. Insert a memory_chunk row into the database.
      3. Insert media_file rows linked to the chunk.

    Duplicates (same source_id + external_id) are silently skipped.
    Any other error rolls back that item's transaction and re-raises.
    """
    media_svc = MediaService()
    conn = get_connection()

    try:
        for item in inputs:
            source_id = _SOURCE_ID_MAP.get(item.source_type)
            if not source_id:
                print(f"[pipeline] skipping unknown source_type '{item.source_type}'")
                continue

            # Step 1: save media to disk before touching the DB
            saved_media = [
                media_svc.save_pending(pending, item.source_type)
                for pending in item.media
            ]

            try:
                # Step 2: insert memory chunk
                chunk_id = insert_memory_chunk(
                    conn,
                    user_id=_USER_ID,
                    source_id=source_id,
                    external_message_id=item.external_id,
                    content_type=item.content_type,
                    raw_content=item.content,
                    timestamp=item.event_time,
                    participants=item.participants,
                    metadata=item.metadata,
                )

                if chunk_id is None:
                    # ON CONFLICT DO NOTHING — duplicate, skip silently
                    conn.rollback()
                    continue

                conn.commit()

                # Step 3: link media files to the chunk
                for media_obj in saved_media:
                    insert_media_file(conn, chunk_id, media_obj, item.source_type)

                if saved_media:
                    conn.commit()

            except Exception:
                conn.rollback()
                raise

    finally:
        conn.close()
