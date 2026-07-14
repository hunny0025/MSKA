"""
AuditLog ORM model representing append-only logging entries.
"""

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class AuditLog(BaseModel):
    """
    Immutable activity logs tracking critical entity changes (auth, admin, documents).
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "CREATE_PROJECT"
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "project"
    target_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
