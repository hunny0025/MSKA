"""
Pydantic schemas for Document upload metadata, list and retrieve actions.
"""

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    classification: str
    pii_flagged: bool
    status: str
    version: int
    project_id: str
    department_id: str

    class Config:
        from_attributes = True
