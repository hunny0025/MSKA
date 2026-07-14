"""
Unit tests for Notifications polling and status mapping.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from models.notification import Notification
from services.notification_service import get_unread_notifications, mark_as_read


@pytest.mark.asyncio
async def test_get_unread_notifications():
    """Retrieves unread notifications."""
    db_mock = AsyncMock()
    
    notifications = [
        Notification(id="n1", user_id="user-1", message="File indexed", is_read=False),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = notifications
    db_mock.execute.return_value = mock_result

    unread = await get_unread_notifications(db_mock, "user-1")
    
    assert len(unread) == 1
    assert unread[0].message == "File indexed"


@pytest.mark.asyncio
async def test_mark_notification_read():
    """Mark as read updates state flag correctly."""
    db_mock = AsyncMock()
    
    n = Notification(id="n1", user_id="user-1", message="Alert", is_read=False)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = n
    db_mock.execute.return_value = mock_result

    updated = await mark_as_read(db_mock, "n1", "user-1")
    
    assert updated.is_read is True
    # Ensure commit was invoked
    db_mock.commit.assert_called_once()
