"""
FastAPI router for Hybrid Semantic and relational Metadata Search queries.
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import get_current_user
from models.user import User
from services.search_service import search_service

router = APIRouter(prefix="/search", tags=["Enterprise Search"])


@router.get("/")
async def api_search(
    current_user: Annotated[User, Depends(get_current_user)],
    q: str | None = None,
    project_id: str | None = None,
    classification: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a hybrid metadata filter and semantic context search query.
    Enforces user classification clearance gates.
    """
    return await search_service.execute_hybrid_search(
        db,
        query=q,
        project_id=project_id,
        classification_filter=classification,
        user=current_user
    )
