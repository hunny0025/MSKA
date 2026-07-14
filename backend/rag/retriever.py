"""
RAG Retriever mapping semantic database queries and enforcing classification controls.
"""

from typing import Any, Dict, List

from core.permissions import Roles
from models.user import User
from adapters.ai.embeddings import embedding_generator
from adapters.vectorstore.faiss_adapter import vector_store


class Retriever:
    """
    Retrieves candidate context chunks, strictly filtering out any document chunks 
    that violate the user's role-based classification clearance.
    """

    def _get_classification_clearance(self, user_role: str) -> List[str]:
        """
        Determines which data classifications the user is cleared to view.
        
        Clearance Matrix:
        - platform_admin, auditor: restricted, confidential, internal, public
        - project_admin, department_lead: confidential, internal, public
        - employee: internal, public
        """
        if user_role in (Roles.PLATFORM_ADMIN, Roles.AUDITOR):
            return ["restricted", "confidential", "internal", "public"]
        if user_role in (Roles.PROJECT_ADMIN, Roles.DEPARTMENT_LEAD):
            return ["confidential", "internal", "public"]
        return ["internal", "public"]

    def retrieve_relevant_chunks(
        self, 
        project_id: str, 
        query: str, 
        user: User, 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetches similarity search matches from vector index and filters by classification permissions.
        """
        query_vector = embedding_generator.get_embedding(query)
        
        # Query FAISS index namespace
        raw_matches = vector_store.search(project_id, query_vector, top_k=top_k * 2)
        
        # Get clearance labels
        user_clearance = self._get_classification_clearance(user.role.name)
        
        filtered_matches = []
        for match in raw_matches:
            # Metadata structure containing document classification
            doc_meta = match.get("metadata", {})
            classification = doc_meta.get("classification", "internal").lower()
            
            # Authorization barrier (Check if classification is in user's clearance set)
            if classification in user_clearance:
                filtered_matches.append(match)
                
            if len(filtered_matches) >= top_k:
                break
                
        return filtered_matches


retriever = Retriever()
export = retriever
