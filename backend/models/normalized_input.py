from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, field_validator

_ALLOWED_CONTENT_TYPES = frozenset({
    "text", "email", "document", "audio", "gmeet"
})


class PendingMedia(BaseModel):
    raw_bytes: bytes
    original_filename: str
    mime_type: str
    captured_at: datetime


class NormalizedInput(BaseModel):
    source_type: str
    external_id: str
    content: str
    content_type: str
    event_time: datetime
    participants: List[str]
    metadata: Dict[str, Any]
    media: List[PendingMedia] = []

    @field_validator("content_type")
    @classmethod
    def content_type_allowed(cls, v: str) -> str:
        if v not in _ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"content_type '{v}' is not allowed. "
                f"Must be one of: {sorted(_ALLOWED_CONTENT_TYPES)}"
            )
        return v

    @field_validator("source_type")
    @classmethod
    def source_type_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_type must not be empty")
        return v

    @field_validator("external_id")
    @classmethod
    def external_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("external_id must not be empty")
        return v

    @field_validator("participants", mode="before")
    @classmethod
    def participants_default_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        return v
