"""
Analytics and activity reporting logic layer.
"""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.permissions import Roles
from models.document import Document
from models.chat import ChatMessage
from models.audit import AuditLog
from models.user import User


async def get_dashboard_stats(db: AsyncSession) -> dict:
    """
    Computes global metrics for files, chats and quarantines.
    """
    # Count approved documents
    app_query = select(func.count(Document.id)).where(Document.status == "approved")
    app_res = await db.execute(app_query)
    approved_count = app_res.scalar() or 0

    # Count quarantined documents
    q_query = select(func.count(Document.id)).where(Document.status == "quarantined")
    q_res = await db.execute(q_query)
    quarantined_count = q_res.scalar() or 0

    # Count total chat questions submitted
    chat_query = select(func.count(ChatMessage.id)).where(ChatMessage.role == "user")
    chat_res = await db.execute(chat_query)
    chat_count = chat_res.scalar() or 0

    # Count distinct active users
    user_query = select(func.count(func.distinct(AuditLog.user_id)))
    user_res = await db.execute(user_query)
    active_users = user_res.scalar() or 0

    return {
        "total_approved_docs": approved_count,
        "total_quarantined_docs": quarantined_count,
        "total_queries": chat_count,
        "active_users": active_users
    }


async def get_recent_activities(db: AsyncSession, user: User, limit: int = 10) -> list:
    """
    Fetches latest audit actions. Standard employees can only see their own actions,
    while platform administrators and compliance auditors see all logs.
    """
    query = select(AuditLog)
    
    if user.role.name not in (Roles.PLATFORM_ADMIN, Roles.AUDITOR):
        # Scope strictly to user's actions
        query = query.where(AuditLog.user_id == user.id)
        
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    result = await db.execute(query)
    logs = list(result.scalars().all())

    # Map details to human-readable strings
    activity_feed = []
    for log in logs:
        activity_feed.append({
            "id": log.id,
            "action": log.action,
            "target_type": log.target_type,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "details": log.details
        })
    return activity_feed

