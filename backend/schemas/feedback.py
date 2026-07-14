"""
Pydantic schemas for Feedback requests and responses.
"""

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    message_id: str
    thumbs_up: bool
    comment: str | None = Field(None, max_length=500)


class FeedbackOut(BaseModel):
    id: str
    message_id: str
    thumbs_up: bool
    comment: str | None

    class Config:
        from_attributes = True
