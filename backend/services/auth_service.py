"""
Authentication and identity mapping operations.
"""

from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.security import verify_password, hash_password, create_access_token, create_refresh_token, verify_token_type
from models.user import User
from models.role import Role
from schemas.auth import UserLogin, UserCreate, Token


async def seed_roles(db: AsyncSession) -> None:
    """
    Populates roles table on application setup if blank.
    """
    role_names = ["platform_admin", "project_admin", "department_lead", "employee", "auditor"]
    descriptions = {
        "platform_admin": "Full system configuration root manager",
        "project_admin": "Project catalog database administrator",
        "department_lead": "Scoped department workflow manager",
        "employee": "Regular system dashboard query operator",
        "auditor": "Compliance logs auditor read-only account"
    }

    for name in role_names:
        query = select(Role).where(Role.name == name)
        result = await db.execute(query)
        role = result.scalar_one_or_none()
        if not role:
            new_role = Role(name=name, description=descriptions[name])
            db.add(new_role)
    await db.commit()


async def authenticate_user(db: AsyncSession, credentials: UserLogin) -> User:
    """
    Validates user log in request against username and bcrypt password database.
    """
    query = select(User).where(User.username == credentials.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    await db.refresh(user, ["role"])

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def register_new_user(db: AsyncSession, payload: UserCreate) -> User:
    """
    Creates a new user record inside database.
    """
    # Check duplicate username
    user_query = select(User).where(User.username == payload.username)
    res = await db.execute(user_query)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check duplicate email
    email_query = select(User).where(User.email == payload.email)
    res = await db.execute(email_query)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate role id
    role_query = select(Role).where(Role.id == payload.role_id)
    res = await db.execute(role_query)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected Role not found"
        )

    hashed_pw = hash_password(payload.password)
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_pw,
        role_id=payload.role_id,
        is_active=True
    )

    db.add(user)
    await db.commit()
    await db.refresh(user, ["role"])
    return user


async def create_tokens_for_user(user: User) -> Token:
    """
    Returns signed Access & Refresh token structures for verified sessions.
    """
    payload = {"sub": user.username, "role": user.role.name, "user_id": user.id}
    access_token = create_access_token(data=payload)
    refresh_token = create_refresh_token(data=payload)
    return Token(access_token=access_token, refresh_token=refresh_token)


async def refresh_session_tokens(db: AsyncSession, refresh_token: str) -> Token:
    """
    Decodes the refresh token and generates a new pair of access/refresh tokens.
    """
    try:
        payload = verify_token_type(refresh_token, "refresh")
        username: str = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session is invalid"
        )

    await db.refresh(user, ["role"])
    return await create_tokens_for_user(user)
