"""
C1 — Retrieval Trace Orchestrator.

Augments the standard RAG response with a full trace object containing:
  - the raw chunks retrieved (pre-rerank)
  - the reranked chunks (post-rerank)
  - per-chunk scores and metadata
  - confidence report
  - whether the AI call was skipped (abstain)

Used by the trace API endpoint so the frontend can render a transparent
view of exactly which documents influenced an answer.
"""
from __future__ import annotations

from typing import Any

from models.user import User
from rag.reranker import reranker
from rag.confidence import confidence_engine
from adapters.ai.factory import ai_provider
from services.isolation_service import isolated_retriever


class TraceOrchestrator:
    """
    Like RAGOrchestrator but returns a detailed trace dict alongside the answer.
    Shares the same isolation, reranking, and confidence gates.
    """

    async def execute_with_trace(
        self,
        project_id: str,
        query: str,
        user: User,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """
        Run the full RAG pipeline and return both the answer and a trace.

        Returns:
        {
          "answer":           str,
          "confidence_score": float,
          "should_abstain":   bool,
          "citations":        [...],
          "trace": {
            "raw_chunks":     [...],   # pre-rerank
            "reranked_chunks":[...],   # post-rerank
            "confidence":     {...},   # full report from confidence engine
            "ai_called":      bool,
          }
        }
        """
        # 1. Project-isolated retrieval (B1)
        raw_chunks = isolated_retriever.search(project_id, query, user, top_k=top_k)

        # 2. Rerank
        reranked_chunks = reranker.rerank(query, raw_chunks)

        # 3. Confidence
        conf_report = confidence_engine.calculate_confidence(reranked_chunks)

        # 4. AI call (or abstain)
        ai_called = not conf_report["should_abstain"]
        if ai_called:
            answer = await ai_provider.generate_response(query, reranked_chunks)
        else:
            answer = "I do not have enough verified information to answer your request."

        citations = [
            {
                "document_id": c.get("metadata", {}).get("document_id"),
                "filename":    c.get("metadata", {}).get("filename"),
                "chunk_id":    c.get("id"),
                "score":       round(c.get("score", 0.0), 4),
                "text":        c.get("text", ""),
                "classification": c.get("metadata", {}).get("classification", "internal"),
            }
            for c in reranked_chunks
        ] if ai_called else []

        return {
            "answer":           answer,
            "confidence_score": conf_report["score"],
            "should_abstain":   conf_report["should_abstain"],
            "citations":        citations,
            "trace": {
                "raw_chunks": [
                    {
                        "id":    c.get("id"),
                        "score": round(c.get("score", 0.0), 4),
                        "text":  c.get("text", "")[:300],   # truncate for wire safety
                        "metadata": c.get("metadata", {}),
                    }
                    for c in raw_chunks
                ],
                "reranked_chunks": [
                    {
                        "id":    c.get("id"),
                        "score": round(c.get("score", 0.0), 4),
                        "text":  c.get("text", "")[:300],
                        "metadata": c.get("metadata", {}),
                    }
                    for c in reranked_chunks
                ],
                "confidence": conf_report,
                "ai_called":  ai_called,
            },
        }


trace_orchestrator = TraceOrchestrator()
