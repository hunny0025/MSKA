"""
Pydantic schemas for Chat requests and responses.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    project_id: str
    title: str = Field("New Chat Session", max_length=200)


class ChatSessionOut(BaseModel):
    id: str
    title: str
    project_id: str
    user_id: str

    class Config:
        from_attributes = True


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: List[Dict[str, Any]] | None = None
    confidence_score: float | None = None

    class Config:
        from_attributes = True


class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1)


class ExplainSimplyRequest(BaseModel):
    message_id: str
