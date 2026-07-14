"""
Document ORM model tracking files and status mapping.
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.project import Project


class Document(BaseModel):
    """
    Document metadata tracking physical files, versioning, data classification, and PII status.
    """

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(512), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Classification labels: public, internal, confidential, restricted
    classification: Mapped[str] = mapped_column(String(50), default="internal", nullable=False)
    
    # Ingestion check fields
    pii_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # approved, quarantined, pending
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project")
