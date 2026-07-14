"""
FastAPI router for Departments CRUD.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import PermissionChecker, Roles, get_current_user
from models.user import User
from schemas.department import DepartmentCreate, DepartmentOut
from services.department_service import create_department, get_departments, get_department_by_id

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def api_create_department(
    payload: DepartmentCreate,
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new organization department. Restricted to platform_admin.
    """
    return await create_department(db, payload, current_user.id)


@router.get("/", response_model=list[DepartmentOut])
async def api_get_departments(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all departments. Allowed for all logged in users.
    """
    return await get_departments(db)


@router.get("/{dept_id}", response_model=DepartmentOut)
async def api_get_department(
    dept_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches details of a specific department.
    """
    return await get_department_by_id(db, dept_id)
