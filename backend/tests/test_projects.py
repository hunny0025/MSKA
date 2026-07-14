"""
Unit tests for Project business rules and permission filters.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.permissions import Roles
from models.project import Project
from models.user import User
from models.role import Role
from services.project_service import get_projects_for_user


@pytest.mark.asyncio
async def test_get_projects_for_platform_admin():
    """Platform Admin sees all projects in the system."""
    db_mock = AsyncMock()
    
    # Mock user
    user = User(id="user-1", username="admin")
    user.role = Role(name=Roles.PLATFORM_ADMIN)

    # Mock DB execution
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Project(id="p1", name="Project 1"),
        Project(id="p2", name="Project 2")
      ]
    db_mock.execute.return_value = mock_result

    projects = await get_projects_for_user(db_mock, user)
    
    assert len(projects) == 2
    assert projects[0].name == "Project 1"
    # Ensure query was sent without filters
    db_mock.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_projects_for_department_lead():
    """Department Lead only sees projects matching their department_id."""
    db_mock = AsyncMock()
    
    # Mock user
    user = User(id="user-2", username="lead", department_id="dept-100")
    user.role = Role(name=Roles.DEPARTMENT_LEAD)

    # Mock DB execution
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Project(id="p1", name="Paint Shop Dzire", department_id="dept-100")
    ]
    db_mock.execute.return_value = mock_result

    projects = await get_projects_for_user(db_mock, user)
    
    assert len(projects) == 1
    assert projects[0].department_id == "dept-100"
    db_mock.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_projects_for_employee():
    """Standard Employee only sees projects they are explicitly mapped to."""
    db_mock = AsyncMock()
    
    # Mock user
    user = User(id="user-3", username="worker")
    user.role = Role(name=Roles.EMPLOYEE)

    # Mock DB execution
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Project(id="p3", name="Baleno Facelift")
    ]
    db_mock.execute.return_value = mock_result

    projects = await get_projects_for_user(db_mock, user)
    
    assert len(projects) == 1
    assert projects[0].name == "Baleno Facelift"
    db_mock.execute.assert_called_once()
