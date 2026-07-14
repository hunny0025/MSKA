"""
Pydantic schemas for Notification requests and responses.
"""

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    message: str
    type: str
    is_read: bool

    class Config:
        from_attributes = True
