"""
Abstract base class for AI completion models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAIProvider(ABC):
    """
    Interface for querying LLM generators with context chunks.
    """

    @abstractmethod
    async def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        system_instruction: str | None = None
    ) -> str:
        """
        Submits query + context blocks to LLM and returns the generated answer.
        """
        pass
