"""
Department ORM model representing Maruti Suzuki organizational units (e.g., QA, Production).
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class Department(BaseModel):
    """
    Department entity mapping groups of users, projects, and documents.
    """

    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="department", cascade="all, delete-orphan")
