"""
Pydantic schemas for Project requests and responses.
"""

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=255)
    department_id: str


class ProjectCreate(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    id: str

    class Config:
        from_attributes = True


class ProjectUserAssign(BaseModel):
    user_id: str
