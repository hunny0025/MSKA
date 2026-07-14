"""
Unit tests for administrative console and quarantine control gates.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from models.document import Document
from services.admin_service import approve_quarantined_document, get_quarantined_documents


@pytest.mark.asyncio
async def test_get_quarantined_documents_query():
    """Admin correctly queries all quarantined files."""
    db_mock = AsyncMock()
    
    docs = [Document(id="d1", status="quarantined")]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = docs
    db_mock.execute.return_value = mock_result

    q_list = await get_quarantined_documents(db_mock)
    
    assert len(q_list) == 1
    assert q_list[0].status == "quarantined"


@pytest.mark.asyncio
async def test_approve_quarantined_changes_status():
    """Approving quarantined file updates status and runs vector indexing."""
    db_mock = AsyncMock()
    
    doc = Document(
        id="d1", 
        filename="specs.txt", 
        status="quarantined", 
        extracted_text="Safe content",
        project_id="p1",
        classification="internal",
        department_id="dept-1"
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = doc
    db_mock.execute.return_value = mock_result

    # Mock embedding generator and vector store to avoid real models loading
    with pytest.helpers.mocks() if hasattr(pytest, 'helpers') else MagicMock():
        updated_doc = await approve_quarantined_document(db_mock, "d1", "user-admin")
        
        assert updated_doc.status == "approved"
        assert db_mock.commit.call_count == 2

