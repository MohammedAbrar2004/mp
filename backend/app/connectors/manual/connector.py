from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput, PendingMedia


def _infer_content_type(media: List[PendingMedia]) -> str:
    """
    Derive content_type from attached media.
    Falls back to 'text' when there is no media.
    """
    if not media:
        return "text"
    first_mime = media[0].mime_type
    if first_mime.startswith("audio/"):
        return "audio"
    if first_mime in ("application/pdf", "application/msword"):
        return "document"
    if "wordprocessingml" in first_mime:
        return "document"
    return "document"


class ManualConnector(BaseConnector):
    def fetch(self) -> List[NormalizedInput]:
        return []

    def create_input(
        self,
        content: str,
        participants: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        media: Optional[List[PendingMedia]] = None,
    ) -> NormalizedInput:
        media = media or []
        content_type = _infer_content_type(media)

        return NormalizedInput(
            source_type="manual",
            external_id=str(uuid4()),
            content=content,
            content_type=content_type,
            event_time=datetime.now(timezone.utc),
            participants=participants,
            metadata=metadata or {},
            media=media,
        )
