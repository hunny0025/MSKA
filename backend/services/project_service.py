"""
Project business logic service.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.permissions import Roles
from models.project import Project
from models.user import User
from schemas.project import ProjectCreate
from services.audit_service import log_activity


async def create_project(db: AsyncSession, payload: ProjectCreate, user_id: str) -> Project:
    """
    Creates a new isolated project and logs activity.
    """
    # Check duplicate name
    query = select(Project).where(Project.name == payload.name)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with name '{payload.name}' already exists"
        )

    proj = Project(
        name=payload.name,
        description=payload.description,
        department_id=payload.department_id
    )

    db.add(proj)
    await db.commit()
    await db.refresh(proj)

    await log_activity(
        db, 
        user_id=user_id, 
        action="CREATE_PROJECT", 
        target_type="project", 
        target_id=proj.id,
        details={"name": proj.name, "department_id": proj.department_id}
    )

    return proj


async def get_projects_for_user(db: AsyncSession, user: User) -> list[Project]:
    """
    Lists projects scoped by permissions:
    - platform_admin/auditor: see all projects.
    - project_admin/department_lead: see projects within their department.
    - employee: see projects they are assigned to.
    """
    if user.role.name in (Roles.PLATFORM_ADMIN, Roles.AUDITOR):
        query = select(Project)
    elif user.role.name in (Roles.PROJECT_ADMIN, Roles.DEPARTMENT_LEAD):
        if not user.department_id:
            return []  # Isolated user with no department mapping
        query = select(Project).where(Project.department_id == user.department_id)
    else:
        # standard employee: M2M query via project_users
        query = select(Project).join(Project.users).where(User.id == user.id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def assign_user_to_project(db: AsyncSession, project_id: str, target_user_id: str, acting_user_id: str) -> Project:
    """
    Maps a user to a project database context.
    """
    # Get project
    proj_query = select(Project).options(selectinload(Project.users)).where(Project.id == project_id)
    res = await db.execute(proj_query)
    project = res.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Get user
    user_query = select(User).where(User.id == target_user_id)
    res = await db.execute(user_query)
    user = res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user in project.users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already assigned to project")

    project.users.append(user)
    await db.commit()

    await log_activity(
        db, 
        user_id=acting_user_id, 
        action="ASSIGN_USER_TO_PROJECT", 
        target_type="project", 
        target_id=project.id,
        details={"assigned_user_id": target_user_id}
    )

    return project
