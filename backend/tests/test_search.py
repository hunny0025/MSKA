"""
Unit tests for hybrid search logic and document relationship mapping.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.permissions import Roles
from models.document import Document
from models.user import User
from models.role import Role
from services.search_service import search_service


@pytest.mark.asyncio
async def test_search_confidentiality_barrier():
    """Employees should not be able to retrieve confidential search results."""
    db_mock = AsyncMock()

    # User Employee
    user = User(id="user-1", username="worker")
    user.role = Role(name=Roles.EMPLOYEE)

    # Matched documents in DB (one confidential, one public)
    doc_public = Document(id="d1", filename="pub.pdf", classification="public", status="approved")
    doc_conf = Document(id="d2", filename="secret.pdf", classification="confidential", status="approved")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [doc_public, doc_conf]
    db_mock.execute.return_value = mock_result

    # Search with no query (triggers metadata filter scan)
    results = await search_service.execute_hybrid_search(
        db_mock,
        query=None,
        project_id=None,
        classification_filter=None,
        user=user
    )

    # Employee should only see the public document
    assert len(results) == 1
    assert results[0]["document"]["filename"] == "pub.pdf"


@pytest.mark.asyncio
async def test_search_relations_supersede():
    """Verify document search output populates correct version relationships."""
    db_mock = AsyncMock()

    # Admin User (clearance for all)
    user = User(id="user-admin")
    user.role = Role(name=Roles.PLATFORM_ADMIN)

    # Set of documents representing two versions of the same file
    doc_v1 = Document(id="d1", filename="manual.pdf", version=1, project_id="p1", status="approved", classification="internal")
    doc_v2 = Document(id="d2", filename="manual.pdf", version=2, project_id="p1", status="approved", classification="internal")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [doc_v1, doc_v2]
    db_mock.execute.return_value = mock_result

    results = await search_service.execute_hybrid_search(
        db_mock,
        query=None,
        project_id="p1",
        classification_filter=None,
        user=user
    )

    # Results should map relations: d1 is superseded by d2; d2 supersedes d1
    d1_match = next(r for r in results if r["document"]["id"] == "d1")
    d2_match = next(r for r in results if r["document"]["id"] == "d2")

    assert len(d1_match["relationships"]["superseded_by"]) == 1
    assert d1_match["relationships"]["superseded_by"][0]["id"] == "d2"

    assert len(d2_match["relationships"]["supersedes"]) == 1
    assert d2_match["relationships"]["supersedes"][0]["id"] == "d1"
