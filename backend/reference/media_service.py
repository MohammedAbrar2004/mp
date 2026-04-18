"""
Media service for EchoMind.
Handles saving and organizing media files (images, audio, documents, video).
Shared utility used by all connectors - no connector-specific logic.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


@dataclass
class MediaObject:
    """Represents a saved media file with metadata."""
    local_path: str
    original_filename: str
    media_type: str        # image | audio | document | video
    mime_type: str
    size_bytes: int
    source_type: str       # whatsapp | gmail | gmeet | manual
    captured_at: datetime


class MediaService:
    """
    Service for saving and managing media files.
    Organizes files by type and provides metadata tracking.
    """
    
    # Mapping from MIME types to media categories
    MIME_TO_MEDIA_TYPE = {
        "image/jpeg": "image",
        "image/png": "image",
        "image/webp": "image",
        "audio/ogg": "audio",
        "audio/mpeg": "audio",
        "audio/mp4": "audio",
        "audio/wav": "audio",
        "application/pdf": "document",
        "application/msword": "document",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
        "application/vnd.ms-excel": "document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "document",
        "video/mp4": "video",
    }
    
    def __init__(self):
        """Initialize MediaService with base directory configuration."""
        self.base_dir = os.getenv("MEDIA_BASE_DIR", "./media")
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create media subdirectories if they don't exist."""
        subdirs = ["images", "audio", "documents", "video"]
        for subdir in subdirs:
            dir_path = os.path.join(self.base_dir, subdir)
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _get_media_type_dir(self, media_type: str) -> str:
        """
        Map media_type to the correct subdirectory.
        
        Args:
            media_type: One of 'image', 'audio', 'document', 'video'
            
        Returns:
            Subdirectory name
        """
        mapping = {
            "image": "images",
            "audio": "audio",
            "document": "documents",
            "video": "video",
        }
        return mapping.get(media_type, "documents")
    
    def _get_file_extension(self, original_filename: str) -> str:
        """Extract file extension from original filename."""
        _, ext = os.path.splitext(original_filename)
        return ext if ext else ""
    
    def save(
        self,
        raw_bytes: bytes,
        original_filename: str,
        mime_type: str,
        source_type: str,
        captured_at: datetime
    ) -> MediaObject:
        """
        Save media file and return MediaObject with metadata.
        
        Args:
            raw_bytes: File content as bytes
            original_filename: Original filename from source
            mime_type: MIME type of the file
            source_type: Source type (whatsapp, gmail, gmeet, manual)
            captured_at: When the media was captured
            
        Returns:
            MediaObject with file path and metadata
            
        Raises:
            ValueError: If mime_type is not supported
        """
        # Validate mime_type
        if mime_type not in self.MIME_TO_MEDIA_TYPE:
            raise ValueError(
                f"Unsupported mime_type '{mime_type}'. "
                f"Supported types: {', '.join(self.MIME_TO_MEDIA_TYPE.keys())}"
            )
        
        # Detect media_type from mime_type
        media_type = self.MIME_TO_MEDIA_TYPE[mime_type]
        
        # Generate unique filename
        file_extension = self._get_file_extension(original_filename)
        unique_filename = f"{uuid4()}{file_extension}"
        
        # Determine target directory
        subdir = self._get_media_type_dir(media_type)
        target_dir = os.path.join(self.base_dir, subdir)
        local_path = os.path.join(target_dir, unique_filename)
        
        # Ensure directory exists
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(local_path, "wb") as f:
            f.write(raw_bytes)
        
        # Return MediaObject
        return MediaObject(
            local_path=local_path,
            original_filename=original_filename,
            media_type=media_type,
            mime_type=mime_type,
            size_bytes=len(raw_bytes),
            source_type=source_type,
            captured_at=captured_at,
        )
