"""
Manual connector for EchoMind.
Handles user-uploaded documents and manual entries through file system or API.
Normalizes to NormalizedInput format.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
import json
from app.connectors.base_connector import BaseConnector
from app.services.media_service import MediaService
from models.normalized_input import NormalizedInput

logger = logging.getLogger("EchoMind.Manual")


class ManualConnector(BaseConnector):
    """Manual data connector for user-uploaded documents and entries."""
    
    # Directory where manually uploaded files are stored
    MANUAL_UPLOAD_DIR = "data/manual_uploads"
    
    # State file to track processed files
    STATE_FILE = "data/manual_state.json"
    
    def __init__(self):
        """Initialize Manual connector with upload directory."""
        super().__init__()
        self.media_service = MediaService()
        self._ensure_upload_dir()
        self._load_state()
    
    def _ensure_upload_dir(self):
        """Ensure manual upload directory exists."""
        Path(self.MANUAL_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Manual: Ensured upload directory exists at {self.MANUAL_UPLOAD_DIR}")
    
    def _load_state(self):
        """Load processing state to track which files have been processed."""
        self.processed_files = set()
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                logger.debug(f"Manual: Loaded state with {len(self.processed_files)} processed files")
            except Exception as e:
                logger.warning(f"Manual: Failed to load state file: {e}")
                self.processed_files = set()
    
    def _save_state(self):
        """Save processing state to file."""
        try:
            Path(self.STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
            with open(self.STATE_FILE, 'w') as f:
                json.dump({'processed_files': list(self.processed_files)}, f)
            logger.debug(f"Manual: Saved state with {len(self.processed_files)} processed files")
        except Exception as e:
            logger.warning(f"Manual: Failed to save state file: {e}")
    
    def fetch_data(self) -> list[NormalizedInput]:
        """
        Scan manual upload directory for new files.
        Process each file and create NormalizedInput objects.
        Mark processed files to avoid re-processing.
        """
        results = []
        
        if not os.path.isdir(self.MANUAL_UPLOAD_DIR):
            logger.warning(f"Manual: Upload directory not found: {self.MANUAL_UPLOAD_DIR}")
            return results
        
        try:
            # Scan directory for files
            all_files = []
            for item in os.listdir(self.MANUAL_UPLOAD_DIR):
                item_path = os.path.join(self.MANUAL_UPLOAD_DIR, item)
                if os.path.isfile(item_path):
                    all_files.append(item)
            
            logger.info(f"Manual: Found {len(all_files)} files in upload directory")
            
            # Process each unprocessed file
            for filename in all_files:
                file_path = os.path.join(self.MANUAL_UPLOAD_DIR, filename)
                
                # Skip if already processed
                if filename in self.processed_files:
                    logger.debug(f"Manual: Skipping already-processed file: {filename}")
                    continue
                
                try:
                    # Parse metadata from filename if present
                    # Format: title__metadata.ext or just filename
                    title, metadata = self._parse_filename(filename)
                    
                    # Read file content
                    with open(file_path, 'rb') as f:
                        file_bytes = f.read()
                    
                    # Determine MIME type from extension
                    mime_type = self._get_mime_type(filename)
                    
                    # Get file creation time
                    file_stat = os.stat(file_path)
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    # Try to extract text content
                    content_text = self._extract_text_content(filename, file_bytes)
                    
                    # Save via MediaService if it's a binary file
                    media_objects = None
                    if mime_type and mime_type != 'text/plain':
                        try:
                            media_obj = self.media_service.save(
                                raw_bytes=file_bytes,
                                original_filename=filename,
                                mime_type=mime_type,
                                source_type="manual",
                                captured_at=file_time
                            )
                            media_objects = [media_obj]
                            logger.info(f"Manual: Saved {filename} via MediaService")
                        except Exception as e:
                            logger.warning(f"Manual: Could not save {filename} as media: {e}")
                    
                    # Create NormalizedInput
                    content_type = self._get_content_type(filename)
                    
                    results.append(NormalizedInput(
                        source_type="manual",
                        external_message_id=filename,  # Filename as unique ID
                        timestamp=file_time,
                        participants=["user"],
                        content_type=content_type,
                        raw_content=content_text,
                        metadata={
                            "origin": "manual_upload",
                            "file_name": filename,
                            "file_size_bytes": len(file_bytes),
                            "mime_type": mime_type,
                            **metadata  # Include parsed metadata
                        },
                        media=media_objects
                    ))
                    
                    # Mark as processed
                    self.processed_files.add(filename)
                    logger.info(f"Manual: Processed file '{filename}'")
                    
                except Exception as e:
                    logger.error(f"Manual: Failed to process file {filename}: {e}")
                    continue
            
            # Save state after processing
            self._save_state()
            
            logger.info(f"Manual: Successfully processed {len(results)} items")
            return results
        
        except Exception as e:
            logger.error(f"Manual: Unexpected error: {e}")
            return results
    
    def _parse_filename(self, filename: str) -> tuple[str, dict]:
        """
        Parse metadata from filename.
        Format: "title__tag1,tag2__description.ext" -> title, {tags: [...], description: ...}
        Simple format: just filename -> filename as title, empty metadata
        """
        name_without_ext = os.path.splitext(filename)[0]
        parts = name_without_ext.split('__')
        
        title = parts[0] if parts else filename
        metadata = {}
        
        if len(parts) > 1:
            # Parse tags from second segment
            if len(parts) > 1:
                tags_str = parts[1] if len(parts) > 1 else ""
                if tags_str:
                    metadata['tags'] = [t.strip() for t in tags_str.split(',')]
        
        if len(parts) > 2:
            # Parse description from third segment
            metadata['user_description'] = parts[2]
        
        return title, metadata
    
    def _get_mime_type(self, filename: str) -> str:
        """Determine MIME type from file extension."""
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
        }
        
        ext = os.path.splitext(filename)[1].lower()
        return mime_types.get(ext, '')
    
    def _get_content_type(self, filename: str) -> str:
        """Determine NormalizedInput content_type from file extension."""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            return 'image'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            return 'audio'
        elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
            return 'document'
        else:
            return 'text'
    
    def _extract_text_content(self, filename: str, file_bytes: bytes) -> str:
        """
        Extract text content from file.
        For text files this is straightforward, for binary formats we extract metadata.
        """
        ext = os.path.splitext(filename)[1].lower()
        
        # For plain text files
        if ext == '.txt':
            try:
                return file_bytes.decode('utf-8', errors='ignore')
            except:
                return f"[Binary text file: {filename}]"
        
        # For documents and other files, return metadata summary
        return f"Document: {filename} ({len(file_bytes)} bytes)"
