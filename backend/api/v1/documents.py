"""
FastAPI router for Document uploads and metadata queries.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import PermissionChecker, Roles, get_current_user
from models.user import User
from schemas.document import DocumentOut
from services.document_service import ingest_document, get_documents_by_project, get_document_by_id

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def api_upload_document(
    file: UploadFile,
    project_id: Annotated[str, Form(...)],
    department_id: Annotated[str, Form(...)],
    classification: Annotated[str, Form(...)],
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN, Roles.PROJECT_ADMIN, Roles.DEPARTMENT_LEAD]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a manual database document. Guarded for creators.
    """
    return await ingest_document(
        db,
        upload_file=file,
        project_id=project_id,
        department_id=department_id,
        user_provided_classification=classification,
        user_id=current_user.id
    )


@router.get("/project/{project_id}", response_model=list[DocumentOut])
async def api_get_project_documents(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Lists documents indexed within a specific isolated project scope.
    """
    return await get_documents_by_project(db, project_id)


@router.get("/{doc_id}", response_model=DocumentOut)
async def api_get_document(
    doc_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches detail metadata of a specific document.
    """
    return await get_document_by_id(db, doc_id)
