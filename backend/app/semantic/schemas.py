from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str
    type: Literal[
        "person", "project", "organization", "tool", "technology",
        "topic", "task", "location", "file", "concept"
    ]


class Event(BaseModel):
    title: str
    summary: Optional[str] = None
    event_type: Literal["decision", "meeting", "task", "discussion", "milestone", "other"]
    timestamp: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class Relationship(BaseModel):
    entity: str
    role: Literal["participant", "subject", "organizer", "mentioned", "owner", "assignee", "reporter"]


class SemanticOutput(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    event: Optional[Event] = None
    relationships: List[Relationship] = Field(default_factory=list)
    refined_salience: float
