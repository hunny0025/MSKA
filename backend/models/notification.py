"""
Notification ORM model tracking user notifications.
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class Notification(BaseModel):
    """
    User notifications for RAG ingestion alerts and system warnings.
    """

    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="info", nullable=False)  # info, success, warning, danger
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
