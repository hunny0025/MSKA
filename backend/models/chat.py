"""
ChatSession, ChatMessage, and BookmarkedMessage ORM models tracking user-AI interactions.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class ChatSession(BaseModel):
    """
    Session container isolating message history for a user within a project workspace.
    """

    __tablename__ = "chat_sessions"

    title: Mapped[str] = mapped_column(String(200), default="New Chat Session", nullable=False)
    
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", 
        back_populates="session", 
        cascade="all, delete-orphan", 
        order_by="ChatMessage.created_at"
    )


class ChatMessage(BaseModel):
    """
    Message logs inside a ChatSession containing user prompts and AI responses with citations.
    """

    __tablename__ = "chat_messages"

    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # RAG metadata (Pydantic serialized to JSON list of citation chunks)
    citations: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")


class BookmarkedMessage(BaseModel):
    """
    User-bookmarked messages for quick references from the dashboard.
    """

    __tablename__ = "bookmarked_messages"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[str] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
