"""
NormalizedInput model for EchoMind.
Universal data contract for all connectors.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, field_validator
from app.services.media_service import MediaObject


class NormalizedInput(BaseModel):
    """
    Universal data contract for ingestion.
    All connectors must convert raw data into this format.
    """
    
    source_type: str
    external_message_id: str
    timestamp: datetime
    participants: list[str]
    content_type: Literal["text", "transcript", "email", "document", "audio", "image"]
    raw_content: str
    metadata: dict = {}
    media: list[MediaObject] | None = None
    
    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        """Validate content_type is one of the allowed values."""
        allowed = {"text", "transcript", "email", "document", "audio", "image"}
        if v not in allowed:
            raise ValueError(f"content_type must be one of {allowed}")
        return v
    
    @field_validator("participants", mode="before")
    @classmethod
    def validate_participants(cls, v):
        """Ensure participants is always a list."""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("participants must be a list")
        return v
    
    def to_dict(self):
        """Convert model to dictionary."""
        return self.model_dump()
