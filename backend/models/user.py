"""
User ORM model containing authentication credentials and relationship to roles.
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.role import Role


class User(BaseModel):
    """
    User entity for identity verification, session management, and RBAC evaluation.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    
    # Track department membership (for department level RBAC, mapped in future database schema)
    department_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
