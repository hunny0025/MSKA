"""
FastAPI router for identity credentials authentication and role queries.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import get_current_user, PermissionChecker, Roles
from schemas.auth import Token, UserCreate, UserOut, UserLogin
from services.auth_service import authenticate_user, register_new_user, create_tokens_for_user, refresh_session_tokens, seed_roles

router = APIRouter(prefix="/auth", tags=["Identity"])


@router.post("/setup", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def setup_roles(db: AsyncSession = Depends(get_db)):
    """
    Utility endpoint to populate default system roles.
    """
    await seed_roles(db)
    return {"detail": "System roles seeded successfully"}


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Standard OAuth2 password flow login endpoint.
    """
    credentials = UserLogin(username=form_data.username, password=form_data.password)
    user = await authenticate_user(db, credentials)
    return await create_tokens_for_user(user)


@router.post("/login/json", response_model=Token)
async def login_json(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    JSON credentials login endpoint.
    """
    user = await authenticate_user(db, credentials)
    return await create_tokens_for_user(user)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new system user. Restricted to platform_admin in deployment.
    """
    # Open registration is active during pilot phase.
    # In production, this can be guarded:
    # Depends(PermissionChecker([Roles.PLATFORM_ADMIN]))
    user = await register_new_user(db, payload)
    return user


@router.post("/refresh", response_model=Token)
async def refresh_tokens(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """
    Provides rotating tokens refresh mapping.
    """
    return await refresh_session_tokens(db, refresh_token)


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    Retrieves the parsed user details from current session token.
    """
    # Cast to UserOut format
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role_name=current_user.role.name,
        department_id=current_user.department_id,
        is_active=current_user.is_active
    )
