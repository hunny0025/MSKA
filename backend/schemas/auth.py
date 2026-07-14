"""
Pydantic schemas for identity requests and tokens.
"""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Payload decoded from access token."""
    username: str | None = None
    role: str | None = None
    user_id: str | None = None


class UserLogin(BaseModel):
    """User credentials request."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role_id: str


class UserOut(BaseModel):
    """Standard user response."""
    id: str
    username: str
    email: EmailStr
    role_name: str
    department_id: str | None
    is_active: bool

    class Config:
        from_attributes = True
        
class UserProfileUpdate(BaseModel):
    """Update profile data."""
    email: EmailStr | None = None
    password: str | None = None
