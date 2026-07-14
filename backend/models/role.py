"""
Role ORM model representing user access levels.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class Role(BaseModel):
    """
    User roles representing system access levels.

    Standard Roles:
    - employee: Standard lookup/chat access.
    - department_lead: Manage department projects/docs.
    - project_admin: Manage project configs.
    - platform_admin: Full root platform controls.
    - auditor: Compliance-level read-only access.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="role", cascade="all, delete-orphan")
