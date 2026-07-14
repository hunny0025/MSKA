"""
FastAPI router for Notifications polling and status mapping.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import get_current_user
from models.user import User
from schemas.notification import NotificationOut
from services.notification_service import get_unread_notifications, mark_as_read, mark_all_read

router = APIRouter(prefix="/notifications", tags=["System Notifications"])


@router.get("/unread", response_model=list[NotificationOut])
async def api_get_unread(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves unread notifications list. Used by frontend polling widgets.
    """
    return await get_unread_notifications(db, current_user.id)


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def api_mark_read(
    notification_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Sets notification's read state to True.
    """
    return await mark_as_read(db, notification_id, current_user.id)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def api_read_all(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Batch marks all notifications as read.
    """
    await mark_all_read(db, current_user.id)
    return None
