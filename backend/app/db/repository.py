"""
Repository layer for database operations.

Handles all database writes for the ingestion pipeline.
Provides abstraction over direct SQL queries.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Optional, Any
import psycopg2
from psycopg2.extras import Json

from app.services.media_service import MediaObject


def insert_memory_chunk(
    conn,
    user_id: str,
    source_id: str,
    external_message_id: str,
    content_type: str,
    raw_content: str,
    timestamp: datetime,
    participants: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Insert a new memory chunk into the database.

    Args:
        conn: Database connection
        user_id: UUID of the user
        source_id: UUID of the data source
        external_message_id: Unique ID from external system
        content_type: Type of content ('text', 'email', 'document', 'audio', 'gmeet')
        raw_content: Raw content string
        timestamp: When the event occurred
        participants: Optional dict of participants
        metadata: Optional additional metadata
    
    Returns:
        str: UUID of inserted memory chunk, or None if insert failed
        
    Raises:
        psycopg2.Error: On database error
    """
    try:
        cursor = conn.cursor()
        
        memory_chunk_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO memory_chunks (
                id,
                user_id,
                source_id,
                external_message_id,
                timestamp,
                participants,
                content_type,
                raw_content,
                initial_salience,
                metadata,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_id, external_message_id) DO NOTHING
            RETURNING id;
        """

        cursor.execute(query, (
            memory_chunk_id,
            user_id,
            source_id,
            external_message_id,
            timestamp,
            Json(participants) if participants else None,
            content_type,
            raw_content,
            0.0,
            Json(metadata) if metadata else None,
            datetime.utcnow()
        ))
        
        result = cursor.fetchone()
        cursor.close()
        
        return result[0] if result else None
    
    except psycopg2.IntegrityError as e:
        conn.rollback()
        raise psycopg2.IntegrityError(f"Integrity constraint violation: {str(e)}")
    except psycopg2.Error as e:
        conn.rollback()
        raise psycopg2.Error(f"Database error while inserting memory chunk: {str(e)}")


def insert_media_file(conn, chunk_id: str, media: MediaObject, source_type: str) -> None:
    """
    Insert a media file record linked to a memory chunk.

    Args:
        conn: Database connection
        chunk_id: UUID of the parent memory_chunk
        media: MediaObject returned by MediaService.save_pending()
        source_type: Originating source (whatsapp, gmail, etc.)
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO media_files (
                memory_chunk_id,
                original_filename,
                media_type,
                mime_type,
                local_path,
                size_bytes,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                chunk_id,
                media.original_filename,
                media.media_type,
                media.mime_type,
                media.local_path,
                media.size_bytes,
                json.dumps({"source_type": source_type}),
            ),
        )
    finally:
        cursor.close()
