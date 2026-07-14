"""
Mock AI Provider adapter for backend.
"""

from typing import Any, Dict, List
from adapters.ai.ai_provider import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Mock AI provider that assembles answers from retrieved context chunks.
    Allows testing/running without a real LLM.
    """

    async def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        system_instruction: str | None = None
    ) -> str:
        if not context_chunks:
            return "I have no relevant context in the database to answer this question. Please make sure the document is ingested and has correct permissions."

        parts = []
        for chunk in context_chunks:
            chunk_id = chunk.get("id", "unknown")
            text_snippet = chunk.get("text", "")[:300]
            parts.append(f"[{chunk_id}]: {text_snippet}")

        header = f"Mock RAG Answer (Generated from {len(context_chunks)} retrieved chunks):\n\n"
        return header + "\n\n".join(parts)
