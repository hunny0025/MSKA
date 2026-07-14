"""
FastAPI router for Administration and Compliance actions.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import PermissionChecker, Roles, get_current_user
from models.user import User
from schemas.document import DocumentOut
from schemas.feedback import FeedbackCreate, FeedbackOut
from services.admin_service import (
    get_quarantined_documents, approve_quarantined_document, 
    reject_quarantined_document, get_all_audit_logs, submit_feedback, get_all_feedback_records
)

router = APIRouter(prefix="/admin", tags=["Platform Administration"])


@router.get("/quarantine", response_model=list[DocumentOut])
async def api_get_quarantined(
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all PII-flagged quarantined documents. Restricted to platform_admin.
    """
    return await get_quarantined_documents(db)


@router.post("/quarantine/{doc_id}/approve", response_model=DocumentOut)
async def api_approve_document(
    doc_id: str,
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Approves a quarantined document, removing the flag and indexing it.
    """
    return await approve_quarantined_document(db, doc_id, current_user.id)


@router.post("/quarantine/{doc_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def api_reject_document(
    doc_id: str,
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a rejected quarantined document.
    """
    await reject_quarantined_document(db, doc_id, current_user.id)
    return None


@router.get("/audit-logs")
async def api_get_audit(
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN, Roles.AUDITOR]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Returns global activities audit trail. Restricted to platform_admin or compliance auditor.
    """
    return await get_all_audit_logs(db)


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def api_submit_feedback(
    payload: FeedbackCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Submits user review on assistant responses. Accessible to all users.
    """
    return await submit_feedback(
        db, 
        user_id=current_user.id, 
        message_id=payload.message_id, 
        thumbs_up=payload.thumbs_up, 
        comment=payload.comment
    )


@router.get("/feedback", response_model=list[FeedbackOut])
async def api_get_feedback(
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN, Roles.AUDITOR]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Lists global user feedback ratings. Restricted to platform_admin or auditor.
    """
    return await get_all_feedback_records(db)
