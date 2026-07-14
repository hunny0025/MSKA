"""
Deterministic Mock AI Provider for E2E testing.

Returns answers constructed directly from provided context chunks,
ensuring zero API cost and full repeatability. Implements the same
BaseAIProvider interface used by all production adapters.
"""

from typing import Any, Dict, List

from adapters.ai.ai_provider import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Test-only AI provider that echoes back context chunk content
    as a structured answer with inline citation references.

    Behaviour:
    - If context_chunks is empty, returns a canned "no context" response.
    - Otherwise, assembles an answer from chunk texts, prefixed with
      chunk IDs so citation-accuracy tests can verify traceability.
    """

    async def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        system_instruction: str | None = None
    ) -> str:
        if not context_chunks:
            return "I have no relevant context to answer this question."

        parts = []
        for chunk in context_chunks:
            chunk_id = chunk.get("id", "unknown")
            text_snippet = chunk.get("text", "")[:200]
            parts.append(f"[{chunk_id}]: {text_snippet}")

        header = f"Based on {len(context_chunks)} retrieved chunks for query '{query[:80]}':\n\n"
        return header + "\n".join(parts)
