import enum
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.project import Project


class DocumentStatus(str, enum.Enum):
    """Lifecycle statuses for a document processing run."""
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    SCANNING_PII = "scanning_pii"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    READY = "ready"
    QUARANTINED = "quarantined"
    FAILED = "failed"


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
    clearance_level: Mapped[str] = mapped_column(String(50), default="internal", nullable=False)
    
    # Ingestion check fields
    pii_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=DocumentStatus.UPLOADED.value, nullable=False)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    mime_type: Mapped[str] = mapped_column(String(100), default="text/plain", nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project")

    @property
    def file_path(self) -> str:
        return self.filepath

    @file_path.setter
    def file_path(self, value: str):
        self.filepath = value

