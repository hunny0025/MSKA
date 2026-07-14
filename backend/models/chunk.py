"""
Chunk ORM model representing a text passage extracted from a Document.

Adds:
  - text          convenience alias for text_content
  - embedding_json  serialized float vector stored as JSON Text (avoids array type dependency)
"""

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class Chunk(BaseModel):
    """
    ORM representation of a document chunk with embedded vector.
    """

    __tablename__ = "chunks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Primary text storage — `text` is the canonical field used everywhere else
    text: Mapped[str] = mapped_column("text_content", Text, nullable=False)

    # Serialised vector — allows the DB to serve as a fallback index
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
