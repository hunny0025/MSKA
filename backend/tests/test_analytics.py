"""
Unit tests for analytics aggregators and scoping rules in activity feeds.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.permissions import Roles
from models.user import User
from models.role import Role
from models.audit import AuditLog
from services.analytics_service import get_recent_activities, get_dashboard_stats


@pytest.mark.asyncio
async def test_recent_activities_employee_scoping():
    """Employees should only see audit activities matching their own user_id."""
    db_mock = AsyncMock()

    # User Employee
    user = User(id="user-1")
    user.role = Role(name=Roles.EMPLOYEE)

    # Mock return list
    logs = [
        AuditLog(id="a1", user_id="user-1", action="CHAT_QUERY", target_type="session"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = logs
    db_mock.execute.return_value = mock_result

    activities = await get_recent_activities(db_mock, user)
    
    assert len(activities) == 1
    assert activities[0]["action"] == "CHAT_QUERY"


@pytest.mark.asyncio
async def test_recent_activities_admin_global():
    """Administrators retrieve all audit log entities globally."""
    db_mock = AsyncMock()

    # Admin User
    user = User(id="user-admin")
    user.role = Role(name=Roles.PLATFORM_ADMIN)

    # Mock return list containing multiple users actions
    logs = [
        AuditLog(id="a1", user_id="user-1", action="CHAT_QUERY", target_type="session"),
        AuditLog(id="a2", user_id="user-2", action="INGEST_DOCUMENT", target_type="document")
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = logs
    db_mock.execute.return_value = mock_result

    activities = await get_recent_activities(db_mock, user)
    
    assert len(activities) == 2
    # Ensure query was executed (where filter on user_id should be bypassed)
    db_mock.execute.assert_called_once()
