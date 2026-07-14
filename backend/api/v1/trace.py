"""
C1 — Retrieval Trace API Router.

Routes:
  POST /api/v1/projects/{project_id}/trace
      Runs the full pipeline and returns the answer plus a detailed
      retrieval trace object (chunks, scores, confidence, AI gate).

  GET  /api/v1/projects/{project_id}/trace/stream
      SSE version: streams pipeline stages as they complete so the
      frontend can animate the trace panel in real-time.
"""
from __future__ import annotations

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import get_current_user
from models.user import User
from rag.trace_orchestrator import trace_orchestrator
from adapters.ai.embeddings import embedding_generator
from adapters.vectorstore.faiss_adapter import vector_store
from rag.reranker import reranker
from rag.confidence import confidence_engine

router = APIRouter(tags=["Retrieval Trace"])


# ─────────────────────────────────────────────────────────────────────────────
# JSON (single-shot) trace
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/trace")
async def api_query_trace(
    project_id: str,
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Full retrieval trace for a query.

    Body: { "query": "What is the paint defect threshold?" }

    Returns the RAG answer plus a trace object with raw/reranked chunks,
    scores, and confidence report.
    """
    query = (payload.get("query") or "").strip()
    if not query:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="query is required")

    result = await trace_orchestrator.execute_with_trace(project_id, query, current_user)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SSE streaming trace
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/trace/stream")
async def api_query_trace_stream(
    project_id: str,
    query: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    SSE trace stream — emits one event per pipeline stage.

    Stages emitted (in order):
      retrieving  → retrieved  → reranking → reranked →
      confidence  → generating → done

    Each event carries a partial result payload so the UI can render
    results progressively.
    """
    return StreamingResponse(
        _trace_generator(project_id, query, current_user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _trace_generator(project_id: str, query: str, user: User):
    """Yields SSE events for each pipeline stage."""
    from services.isolation_service import isolated_retriever
    from adapters.ai.factory import ai_provider

    def _evt(stage: str, data: dict) -> str:
        return f"event: {stage}\ndata: {json.dumps(data)}\n\n"

    # Stage 1 – embedding + retrieval
    yield _evt("retrieving", {"message": "Searching knowledge base…"})
    await asyncio.sleep(0)  # yield to event loop

    raw_chunks = isolated_retriever.search(project_id, query, user, top_k=10)
    yield _evt("retrieved", {
        "count": len(raw_chunks),
        "chunks": [
            {"id": c.get("id"), "score": round(c.get("score", 0.0), 4), "text": c.get("text", "")[:200]}
            for c in raw_chunks
        ],
    })

    # Stage 2 – reranking
    yield _evt("reranking", {"message": "Reranking results…"})
    await asyncio.sleep(0)

    reranked = reranker.rerank(query, raw_chunks)
    yield _evt("reranked", {
        "count": len(reranked),
        "chunks": [
            {"id": c.get("id"), "score": round(c.get("score", 0.0), 4), "text": c.get("text", "")[:200]}
            for c in reranked
        ],
    })

    # Stage 3 – confidence
    yield _evt("confidence", {"message": "Calculating confidence…"})
    await asyncio.sleep(0)

    conf = confidence_engine.calculate_confidence(reranked)
    yield _evt("confidence_result", conf)

    # Stage 4 – generate
    if conf["should_abstain"]:
        answer = "I do not have enough verified information to answer your request."
        yield _evt("generating", {"message": "Skipped (low confidence)", "ai_called": False})
    else:
        yield _evt("generating", {"message": "Generating answer…", "ai_called": True})
        await asyncio.sleep(0)
        answer = await ai_provider.generate_response(query, reranked)

    # Stage 5 – done
    yield _evt("done", {
        "answer":           answer,
        "confidence_score": conf["score"],
        "should_abstain":   conf["should_abstain"],
        "citations": [
            {"document_id": c.get("metadata", {}).get("document_id"),
             "filename":    c.get("metadata", {}).get("filename"),
             "chunk_id":    c.get("id"),
             "score":       round(c.get("score", 0.0), 4),
             "text":        c.get("text", "")}
            for c in reranked
        ] if not conf["should_abstain"] else [],
    })
