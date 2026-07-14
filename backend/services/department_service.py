"""
Department business logic service.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.department import Department
from schemas.department import DepartmentCreate
from services.audit_service import log_activity


async def create_department(db: AsyncSession, payload: DepartmentCreate, user_id: str) -> Department:
    """
    Creates a new department record and logs the activity.
    """
    # Check duplicate code
    code_query = select(Department).where(Department.code == payload.code)
    res = await db.execute(code_query)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with code '{payload.code}' already exists"
        )

    # Check duplicate name
    name_query = select(Department).where(Department.name == payload.name)
    res = await db.execute(name_query)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department named '{payload.name}' already exists"
        )

    dept = Department(
        name=payload.name,
        code=payload.code,
        description=payload.description
    )

    db.add(dept)
    await db.commit()
    await db.refresh(dept)

    await log_activity(
        db, 
        user_id=user_id, 
        action="CREATE_DEPARTMENT", 
        target_type="department", 
        target_id=dept.id,
        details={"name": dept.name, "code": dept.code}
    )

    return dept


async def get_departments(db: AsyncSession) -> list[Department]:
    """
    Lists all departments.
    """
    query = select(Department)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_department_by_id(db: AsyncSession, dept_id: str) -> Department:
    """
    Fetches a department or raises 404.
    """
    query = select(Department).where(Department.id == dept_id)
    result = await db.execute(query)
    dept = result.scalar_one_or_none()
    
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return dept
