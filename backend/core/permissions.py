"""
Role-Based Access Control (RBAC) definitions and dependency check guards.
(AUTH BYPASSED: All routes return dummy admin user)
"""

from typing import Annotated, Sequence
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from models.user import User
from models.role import Role


class Roles:
    """Defined role keys inside the system database."""
    PLATFORM_ADMIN = "platform_admin"
    PROJECT_ADMIN = "project_admin"
    DEPARTMENT_LEAD = "department_lead"
    EMPLOYEE = "employee"
    AUDITOR = "auditor"

    ALL = (PLATFORM_ADMIN, PROJECT_ADMIN, DEPARTMENT_LEAD, EMPLOYEE, AUDITOR)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Decodes the JWT token and fetches the User from the database.
    (MOCKED: Always returns dummy admin user for testing)
    """
    # Fetch admin user along with role association
    query = select(User).where(User.username == "plat_admin_user")
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dummy admin user (plat_admin_user) not found. Please seed the database."
        )
    
    # Load role relationship eagerly
    await db.refresh(user, ["role"])

    return user


class PermissionChecker:
    """
    FastAPI dependency factory class to authorize user roles.
    """

    def __init__(self, allowed_roles: Sequence[str]):
        this_roles = allowed_roles
        # Admin bypass logic (platform_admin is root and can access anything)
        if Roles.PLATFORM_ADMIN not in this_roles:
            this_roles = list(this_roles) + [Roles.PLATFORM_ADMIN]
        self.allowed_roles = this_roles

    def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        """
        Validates user role matches any allowed role inside self.allowed_roles.
        """
        if current_user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this resource"
            )
        return current_user
