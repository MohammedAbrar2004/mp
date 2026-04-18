from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from models.normalized_input import PendingMedia


_MIME_TO_MEDIA_TYPE: dict[str, str] = {
    "audio/ogg": "audio",
    "audio/mpeg": "audio",
    "audio/mp4": "audio",
    "audio/wav": "audio",
    "application/pdf": "document",
    "application/msword": "document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
}

_MIME_TO_EXTENSION: dict[str, str] = {
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/wav": ".wav",
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

_MEDIA_TYPE_TO_DIR: dict[str, str] = {
    "audio": "audio",
    "document": "documents",
}


@dataclass
class MediaObject:
    local_path: str
    original_filename: str
    media_type: str
    mime_type: str
    size_bytes: int
    source_type: str
    captured_at: datetime


def _normalize_mime(raw: str) -> str:
    return raw.split(";")[0].strip().lower()


class MediaService:
    def __init__(self) -> None:
        env_base = os.environ.get("MEDIA_BASE_DIR")
        # backend/app/services/ → three levels up → backend/media/
        self._base_dir = (Path(env_base) if env_base else Path(__file__).parent.parent.parent / "media").resolve()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        for subdir in _MEDIA_TYPE_TO_DIR.values():
            (self._base_dir / subdir).mkdir(parents=True, exist_ok=True)

    def save_pending(self, pending: PendingMedia, source_type: str) -> MediaObject:
        mime = _normalize_mime(pending.mime_type)

        if mime not in _MIME_TO_MEDIA_TYPE:
            raise ValueError(
                f"Unsupported MIME type '{mime}'. "
                f"Supported types: {', '.join(_MIME_TO_MEDIA_TYPE)}"
            )

        media_type = _MIME_TO_MEDIA_TYPE[mime]
        extension = _MIME_TO_EXTENSION.get(mime)
        if extension is None:
            raise ValueError(f"Cannot resolve file extension for MIME type '{mime}'")

        target_dir = self._base_dir / _MEDIA_TYPE_TO_DIR[media_type]
        target_dir.mkdir(parents=True, exist_ok=True)

        local_path = (target_dir / f"{uuid4()}{extension}").resolve()
        local_path.write_bytes(pending.raw_bytes)

        return MediaObject(
            local_path=str(local_path),
            original_filename=pending.original_filename,
            media_type=media_type,
            mime_type=mime,
            size_bytes=len(pending.raw_bytes),
            source_type=source_type,
            captured_at=pending.captured_at,
        )
