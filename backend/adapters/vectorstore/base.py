"""
Abstract base class for Vector database engines.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class BaseVectorStore(ABC):
    """
    Interface for indexing and querying high-dimensional vectors.
    """

    @abstractmethod
    def add_documents(self, project_id: str, documents: List[Dict[str, Any]]) -> None:
        """
        Ingests a list of chunks/documents with their embeddings and metadata.
        
        Args:
            project_id: Namespace separator.
            documents: List of dicts, each containing:
                       - "id": unique chunk ID
                       - "text": chunk string content
                       - "embedding": List[float]
                       - "metadata": dict (e.g. document_id, classification)
        """
        pass

    @abstractmethod
    def search(
        self, 
        project_id: str, 
        query_embedding: List[float], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Finds the closest vectors based on cosine similarity metric.
        
        Returns:
            List of matches, each containing:
            - "id": chunk ID
            - "text": chunk string content
            - "score": float distance metric
            - "metadata": dict
        """
        pass

    @abstractmethod
    def clear_project_namespace(self, project_id: str) -> None:
        """
        Deletes the vector database index associated with a project.
        """
        pass
