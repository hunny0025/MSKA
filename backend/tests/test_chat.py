"""
Unit tests for Chat Services, session ownership rules, and message bookmark mappings.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from core.permissions import Roles
from models.chat import ChatSession, ChatMessage, BookmarkedMessage
from models.user import User
from models.role import Role
from services.chat_service import get_chat_messages, bookmark_message, explain_simply


@pytest.mark.asyncio
async def test_session_ownership_success():
    """Correct session owner retrieves message log successfully."""
    db_mock = AsyncMock()
    
    # Mock session owned by user-10
    session = ChatSession(id="sess-1", user_id="user-10")
    session.messages = [ChatMessage(content="hello")]
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    db_mock.execute.return_value = mock_result

    msgs = await get_chat_messages(db_mock, "sess-1", "user-10")
    assert len(msgs) == 1
    assert msgs[0].content == "hello"


@pytest.mark.asyncio
async def test_session_ownership_denied():
    """Accessing another user's session returns 403 Forbidden exception."""
    db_mock = AsyncMock()
    
    # Mock session owned by user-20
    session = ChatSession(id="sess-1", user_id="user-20")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    db_mock.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await get_chat_messages(db_mock, "sess-1", "user-10")
    
    assert exc.value.status_code == 403
    assert "Unauthorized" in exc.value.detail


@pytest.mark.asyncio
@patch("services.chat_service.ai_provider")
async def test_explain_simply_calls_provider(mock_ai):
    """Explain Simply fetches message content and triggers AI simple response formatting."""
    db_mock = AsyncMock()
    mock_ai.generate_response = AsyncMock(return_value="Simple explanation.")

    # Mock Message
    msg = ChatMessage(id="msg-1", content="Intricate blueprint configuration parameter specifications.")
    msg.session = ChatSession(user_id="user-10")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = msg
    db_mock.execute.return_value = mock_result

    explanation = await explain_simply(db_mock, "msg-1", "user-10")
    
    assert explanation == "Simple explanation."
    mock_ai.generate_response.assert_called_once()
