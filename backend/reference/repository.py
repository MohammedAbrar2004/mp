"""
Repository module for EchoMind database operations.
Owns all raw SQL insert logic for the ingestion pipeline.
Nothing else should write directly to memory_chunks or media_files.
"""

import json
from app.services.media_service import MediaObject


def insert_memory_chunk(cursor, data: dict) -> str:
    """
    Insert a single record into memory_chunks.
    
    Args:
        cursor: psycopg2 database cursor
        data: Dictionary with keys:
            - user_id: UUID of user
            - source_id: UUID of data source
            - external_message_id: ID from source system
            - timestamp: When the message was created
            - participants: List of participant names
            - content_type: Type of content (text, transcript, email, document, audio, image)
            - raw_content: Original message content
            - initial_salience: Salience score
            - metadata: Additional metadata dict
    
    Returns:
        str: The generated memory_chunk UUID
    """
    # Prepare JSON fields
    metadata_json = json.dumps(data["metadata"]) if isinstance(data["metadata"], dict) else data["metadata"]
    participants_json = json.dumps(data["participants"]) if isinstance(data["participants"], list) else data["participants"]
    
    # Insert and return generated ID
    insert_query = """
        INSERT INTO memory_chunks (
            user_id,
            source_id,
            external_message_id,
            timestamp,
            participants,
            content_type,
            raw_content,
            initial_salience,
            metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    
    cursor.execute(insert_query, (
        data["user_id"],
        data["source_id"],
        data["external_message_id"],
        data["timestamp"],
        participants_json,
        data["content_type"],
        data["raw_content"],
        data["initial_salience"],
        metadata_json
    ))
    
    chunk_id = cursor.fetchone()[0]
    return str(chunk_id)


def insert_media_file(cursor, chunk_id: str, media: MediaObject, source_type: str):
    """
    Insert a single record into media_files.
    
    Args:
        cursor: psycopg2 database cursor
        chunk_id: UUID of the associated memory_chunk (from insert_memory_chunk)
        media: MediaObject instance with file metadata
        source_type: Source type (whatsapp, gmail, gmeet, manual, etc)
    """
    metadata_json = json.dumps({"source_type": source_type})
    
    insert_query = """
        INSERT INTO media_files (
            memory_chunk_id,
            original_filename,
            media_type,
            mime_type,
            local_path,
            size_bytes,
            metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query, (
        chunk_id,
        media.original_filename,
        media.media_type,
        media.mime_type,
        media.local_path,
        media.size_bytes,
        metadata_json
    ))
