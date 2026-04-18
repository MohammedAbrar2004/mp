from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput, PendingMedia


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
        return NormalizedInput(
            source_type="manual",
            external_id=str(uuid4()),
            content=content,
            content_type="text",
            event_time=datetime.now(timezone.utc),
            participants=participants,
            metadata=metadata or {},
            media=media or [],
        )
