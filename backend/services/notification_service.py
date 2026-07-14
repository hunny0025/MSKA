"""
Notification business logic service.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.notification import Notification


async def create_notification(
    db: AsyncSession, 
    user_id: str, 
    message: str, 
    severity_type: str = "info"
) -> Notification:
    """
    Spawns a new notification for a user.
    """
    notification = Notification(
        user_id=user_id,
        message=message,
        type=severity_type,
        is_read=False
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def get_unread_notifications(db: AsyncSession, user_id: str) -> list[Notification]:
    """
    Queries unread notification records for a user.
    """
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)
        .order_by(Notification.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def mark_as_read(db: AsyncSession, notification_id: str, user_id: str) -> Notification:
    """
    Sets notification's read state to True.
    """
    query = select(Notification).where(Notification.id == notification_id)
    res = await db.execute(query)
    notification = res.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        
    if notification.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
        
    notification.is_read = True
    await db.commit()
    return notification


async def mark_all_read(db: AsyncSession, user_id: str) -> None:
    """
    Batch marks all user notifications as read.
    """
    query = select(Notification).where(Notification.user_id == user_id).where(Notification.is_read == False)
    res = await db.execute(query)
    notifications = res.scalars().all()
    
    for n in notifications:
        n.is_read = True
    await db.commit()
