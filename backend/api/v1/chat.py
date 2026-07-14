"""
FastAPI router for Chat Session messaging, history, and bookmarks.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import get_current_user
from models.user import User
from schemas.chat import ChatSessionCreate, ChatSessionOut, ChatMessageOut, ChatQuery
from services.chat_service import (
    create_chat_session, get_chat_sessions, get_chat_messages, 
    process_chat_message, explain_simply, bookmark_message, get_bookmarked_messages
)

router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
async def api_create_session(
    payload: ChatSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new chat session scoped to a project.
    """
    return await create_chat_session(db, current_user.id, payload.project_id, payload.title)


@router.get("/sessions/project/{project_id}", response_model=list[ChatSessionOut])
async def api_get_sessions(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all chat sessions owned by the user under a project.
    """
    return await get_chat_sessions(db, current_user.id, project_id)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def api_get_messages(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves message logs for a session. Restricted to session owner.
    """
    return await get_chat_messages(db, session_id, current_user.id)


@router.post("/sessions/{session_id}/query", response_model=ChatMessageOut)
async def api_submit_query(
    session_id: str,
    payload: ChatQuery,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Submits query, triggers retrieval + AI response creation inside session scope.
    """
    return await process_chat_message(db, session_id, payload.query, current_user)


@router.post("/messages/{message_id}/explain", response_model=str)
async def api_explain_simply(
    message_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Applies a second prompt to simplify a message response without re-indexing.
    """
    return await explain_simply(db, message_id, current_user.id)


@router.post("/messages/{message_id}/bookmark", status_code=status.HTTP_201_CREATED)
async def api_bookmark_message(
    message_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Bookmarks a message for quick references.
    """
    await bookmark_message(db, current_user.id, message_id)
    return {"detail": "Message bookmarked successfully"}


@router.get("/bookmarks", response_model=list[ChatMessageOut])
async def api_get_bookmarks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all bookmarked messages for current user.
    """
    return await get_bookmarked_messages(db, current_user.id)
