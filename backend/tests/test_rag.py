"""
Unit tests for RAG pipeline component orchestration and classification filtering.
"""

import pytest
from unittest.mock import patch, MagicMock

from core.permissions import Roles
from models.user import User
from models.role import Role
from rag.retriever import retriever
from rag.reranker import reranker
from rag.confidence import confidence_engine


def test_classification_clearance_mapping():
    """Validates role mapping to exact classification clearance labels."""
    assert "restricted" in retriever._get_classification_clearance(Roles.PLATFORM_ADMIN)
    assert "restricted" in retriever._get_classification_clearance(Roles.AUDITOR)
    
    assert "restricted" not in retriever._get_classification_clearance(Roles.PROJECT_ADMIN)
    assert "confidential" in retriever._get_classification_clearance(Roles.PROJECT_ADMIN)
    
    assert "confidential" not in retriever._get_classification_clearance(Roles.EMPLOYEE)
    assert "internal" in retriever._get_classification_clearance(Roles.EMPLOYEE)


@patch("rag.retriever.vector_store")
@patch("rag.retriever.embedding_generator")
def test_retrieve_classification_filter(mock_embed, mock_store):
    """Retrieve filters out confidential and restricted chunks for standard employees."""
    mock_embed.get_embedding.return_value = [0.1] * 384
    
    # Mock database matches
    mock_store.search.return_value = [
        {"id": "c1", "text": "Public SOP", "score": 0.9, "metadata": {"classification": "public"}},
        {"id": "c2", "text": "Confidential Specs", "score": 0.8, "metadata": {"classification": "confidential"}},
        {"id": "c3", "text": "Restricted Financials", "score": 0.7, "metadata": {"classification": "restricted"}},
        {"id": "c4", "text": "Internal Guide", "score": 0.6, "metadata": {"classification": "internal"}},
    ]

    # Employee user
    user = User(id="u1", username="emp")
    user.role = Role(name=Roles.EMPLOYEE)

    matches = retriever.retrieve_relevant_chunks("proj-1", "test query", user)
    
    # Employee should only see 'public' and 'internal'
    assert len(matches) == 2
    assert matches[0]["id"] == "c1"
    assert matches[1]["id"] == "c4"


def test_reranker_exact_keyword_boost():
    """Reranker boosts scores for exact matches of query words."""
    query = " Dzire brake pad replacement "
    chunks = [
        {"id": "c1", "text": "Vehicle components details overview.", "score": 0.8}, # No overlap
        {"id": "c2", "text": "This covers Dzire brake pad replacement processes.", "score": 0.6} # High overlap
    ]

    results = reranker.rerank(query, chunks)
    
    # c2 should be boosted to the top because of the high query terms overlap
    assert results[0]["id"] == "c2"
    assert results[0]["score"] > results[1]["score"]


def test_confidence_abstention_trigger():
    """Confidence engine flags low-similarity matches for abstention."""
    # Score 0.4 is below default threshold (0.65)
    report = confidence_engine.calculate_confidence([{"id": "c1", "score": 0.4}])
    assert report["should_abstain"] is True

    # Score 0.8 is above default threshold
    report = confidence_engine.calculate_confidence([{"id": "c1", "score": 0.8}])
    assert report["should_abstain"] is False
