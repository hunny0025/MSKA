"""
Feedback ORM model tracking user rating reviews on assistant answers.
"""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class Feedback(BaseModel):
    """
    User reviews tracking quality score indicators (thumbs up/down + text review).
    """

    __tablename__ = "feedbacks"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[str] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    thumbs_up: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
