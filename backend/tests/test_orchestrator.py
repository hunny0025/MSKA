"""
Unit tests for RAG Orchestrator and AI Provider integration.
"""

import pytest
from unittest.mock import AsyncMock, patch

from core.permissions import Roles
from models.user import User
from models.role import Role
from rag.orchestrator import rag_orchestrator


@pytest.mark.asyncio
@patch("rag.orchestrator.retriever")
@patch("rag.orchestrator.ai_provider")
async def test_orchestrator_abstention_skips_ai(mock_ai, mock_retriever):
    """When retrieval has low confidence, the AI provider call is skipped entirely to prevent costs."""
    # Mock no retrieved chunks (empty) -> triggers low confidence / abstention
    mock_retriever.retrieve_relevant_chunks.return_value = []
    
    user = User(id="u1", username="test")
    user.role = Role(name=Roles.EMPLOYEE)

    result = await rag_orchestrator.execute_query("proj-123", " Dzire pricing ", user)

    # Validate output
    assert result["should_abstain"] is True
    assert result["answer"] == "I do not have enough verified information to answer your request."
    assert len(result["citations"]) == 0
    # AI provider MUST NOT have been called
    mock_ai.generate_response.assert_not_called()


@pytest.mark.asyncio
@patch("rag.orchestrator.retriever")
@patch("rag.orchestrator.ai_provider")
async def test_orchestrator_successful_rag_flow(mock_ai, mock_retriever):
    """Successful RAG execution retrieves, calls AI provider, and maps citations."""
    mock_retriever.retrieve_relevant_chunks.return_value = [
        {"id": "doc-1_c0", "text": "Dzire pricing starts from 6 Lakh INR.", "score": 0.9, "metadata": {"document_id": "doc-1", "filename": "dzire_specs.pdf"}}
    ]
    mock_ai.generate_response = AsyncMock(return_value="The Dzire starts at 6 Lakh INR.")

    user = User(id="u1", username="test")
    user.role = Role(name=Roles.EMPLOYEE)

    result = await rag_orchestrator.execute_query("proj-123", "Dzire price", user)

    assert result["should_abstain"] is False
    assert result["answer"] == "The Dzire starts at 6 Lakh INR."
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document_id"] == "doc-1"
    
    # AI provider must be called with the query and chunks
    mock_ai.generate_response.assert_called_once()
