"""
FastAPI router for Projects CRUD and workspace context isolation.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import PermissionChecker, Roles, get_current_user
from models.user import User
from schemas.project import ProjectCreate, ProjectOut, ProjectUserAssign
from services.project_service import create_project, get_projects_for_user, assign_user_to_project

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def api_create_project(
    payload: ProjectCreate,
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN, Roles.PROJECT_ADMIN, Roles.DEPARTMENT_LEAD]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new project. Resticted to platform_admin, project_admin, or department_lead.
    """
    return await create_project(db, payload, current_user.id)


@router.get("/", response_model=list[ProjectOut])
async def api_get_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Lists projects the user has permission to access.
    """
    return await get_projects_for_user(db, current_user)


@router.post("/{project_id}/assign", response_model=ProjectOut)
async def api_assign_user_to_project(
    project_id: str,
    payload: ProjectUserAssign,
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN, Roles.PROJECT_ADMIN]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Maps a user to a project database context.
    """
    return await assign_user_to_project(db, project_id, payload.user_id, current_user.id)
