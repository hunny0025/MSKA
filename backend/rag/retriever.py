"""
RAG Retriever — delegates to the B1 IsolatedRetriever service.

Project isolation and classification RBAC are handled entirely by
isolation_service.IsolatedRetriever; this class is kept as a thin
adaptor so the orchestrator interface stays unchanged.
"""

from typing import Any, Dict, List

from models.user import User
from services.isolation_service import isolated_retriever


class Retriever:
    """
    Thin wrapper that maps the orchestrator's retrieve_relevant_chunks
    call to the project-isolated retriever.
    """

    def retrieve_relevant_chunks(
        self,
        project_id: str,
        query: str,
        user: User,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Returns classification-filtered, project-scoped chunks.
        """
        return isolated_retriever.search(project_id, query, user, top_k=top_k)


retriever = Retriever()
export = retriever
