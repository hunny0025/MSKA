"""
FastAPI router for Dashboard Analytics stats and Activity Feed.
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import get_current_user
from models.user import User
from services.analytics_service import get_dashboard_stats, get_recent_activities

router = APIRouter(prefix="/analytics", tags=["Analytics & Activity"])


@router.get("/stats")
async def api_get_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Returns global metrics for approved/quarantined documents and queries.
    """
    return await get_dashboard_stats(db)


@router.get("/activities")
async def api_get_activities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Returns recent actions feed. Scoped based on permissions.
    """
    return await get_recent_activities(db, current_user)
