"""
Project ORM model representing isolated knowledge bases and workspace context.
"""

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.department import Department

# Many-to-Many association table between Users and Projects
project_users = Table(
    "project_users",
    BaseModel.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Project(BaseModel):
    """
    Project entity. Enforces document, RAG similarity search, and chat context isolation.
    """

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="projects")
    
    # Eagerly list mapped users
    users: Mapped[list["User"]] = relationship("User", secondary=project_users, backref="projects")
