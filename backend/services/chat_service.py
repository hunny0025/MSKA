"""
Chat and conversation history logic layer.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models.chat import ChatSession, ChatMessage, BookmarkedMessage
from models.user import User
from rag.orchestrator import rag_orchestrator
from adapters.ai.factory import ai_provider
from services.audit_service import log_activity


async def create_chat_session(db: AsyncSession, user_id: str, project_id: str, title: str) -> ChatSession:
    """
    Spawns a new chat session.
    """
    session = ChatSession(user_id=user_id, project_id=project_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_chat_sessions(db: AsyncSession, user_id: str, project_id: str) -> list[ChatSession]:
    """
    Lists user's chat sessions in a project scope.
    """
    query = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .where(ChatSession.project_id == project_id)
        .order_by(ChatSession.updated_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_chat_messages(db: AsyncSession, session_id: str, user_id: str) -> list[ChatMessage]:
    """
    Fetches message history or raises 403 on authorization failure.
    """
    query = (
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    )
    res = await db.execute(query)
    session = res.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Ownership verification
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized session access")
        
    return session.messages


async def process_chat_message(db: AsyncSession, session_id: str, query: str, user: User) -> ChatMessage:
    """
    Submits user query, triggers RAG pipelines, and commits chat history.
    """
    # Fetch session
    sess_query = select(ChatSession).where(ChatSession.id == session_id)
    res = await db.execute(sess_query)
    session = res.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    if session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized session access")

    # 1. Save User Message
    user_msg = ChatMessage(session_id=session.id, role="user", content=query)
    db.add(user_msg)
    await db.flush() # Populate ID

    # 2. Run RAG Pipeline
    rag_result = await rag_orchestrator.execute_query(session.project_id, query, user)

    # 3. Save AI Assistant Message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=rag_result["answer"],
        citations=rag_result["citations"],
        confidence_score=rag_result["confidence_score"]
    )
    db.add(assistant_msg)
    
    # Touch session to update updated_at timestamp
    session.title = query[:50] if session.title == "New Chat Session" else session.title
    
    await db.commit()
    await db.refresh(assistant_msg)

    # 4. Audit Log Write (metadata query only, no text logging to protect PII)
    await log_activity(
        db,
        user_id=user.id,
        action="CHAT_QUERY",
        target_type="session",
        target_id=session.id,
        details={
            "query_length": len(query),
            "confidence_score": rag_result["confidence_score"],
            "should_abstain": rag_result["should_abstain"],
            "citation_count": len(rag_result["citations"])
        }
    )

    return assistant_msg


async def explain_simply(db: AsyncSession, message_id: str, user_id: str) -> str:
    """
    Applies a second, cheap prompt template on top of a generated answer for plant-floor workers.
    Does not run vector search.
    """
    # Fetch message
    msg_query = select(ChatMessage).join(ChatMessage.session).where(ChatMessage.id == message_id)
    res = await db.execute(msg_query)
    msg = res.scalar_one_or_none()
    
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        
    if msg.session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized message access")

    # Cheap single completion call
    prompt_instruction = (
        "You are a helpful plant-floor assistant at Maruti Suzuki.\n"
        "Your task is to take the provided text and explain it in extremely simple, "
        "easy-to-understand bullet points for a manufacturing assembly technician. "
        "Remove high-level corporate jargon."
    )
    
    # Context format wrapping the message content directly
    response = await ai_provider.generate_response(
        query=f"Explain simply: {msg.content}",
        context_chunks=[],
        system_instruction=prompt_instruction
    )
    
    return response


async def bookmark_message(db: AsyncSession, user_id: str, message_id: str) -> BookmarkedMessage:
    """
    Bookmarks a chat message for dashboard widgets.
    """
    # Verify message exists
    msg_query = select(ChatMessage).where(ChatMessage.id == message_id)
    res = await db.execute(msg_query)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check already bookmarked
    bm_query = select(BookmarkedMessage).where(BookmarkedMessage.user_id == user_id).where(BookmarkedMessage.message_id == message_id)
    res = await db.execute(bm_query)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message already bookmarked")

    bm = BookmarkedMessage(user_id=user_id, message_id=message_id)
    db.add(bm)
    await db.commit()
    return bm


async def get_bookmarked_messages(db: AsyncSession, user_id: str) -> list[ChatMessage]:
    """
    Lists user bookmarked messages.
    """
    query = (
        select(ChatMessage)
        .join(BookmarkedMessage, ChatMessage.id == BookmarkedMessage.message_id)
        .where(BookmarkedMessage.user_id == user_id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
