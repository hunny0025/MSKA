"""
B1 — Project Isolation Service.

Guarantees that every vector search, document query, and chunk retrieval
is scoped to the caller's project.  No cross-project data leaks regardless
of what document_id or chunk_id is supplied.

Public API
----------
IsolatedRetriever.search(project_id, query, user, top_k)
    Enforces project-scoped FAISS search + RBAC classification filter.

IsolatedRetriever.get_chunk(project_id, chunk_id, db)
    Returns a Chunk only if it belongs to the given project.

IsolatedRetriever.global_search(query, user, db, top_k)
    Cross-project search visible only to PLATFORM_ADMIN / AUDITOR.
    Returns results tagged with their project_id.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.permissions import Roles
from models.chunk import Chunk
from models.user import User
from adapters.ai.embeddings import embedding_generator
from adapters.vectorstore.faiss_adapter import vector_store

logger = logging.getLogger("services.isolation")

# Classification clearance matrix  (same rules as Retriever)
_CLEARANCE: dict[str, list[str]] = {
    Roles.PLATFORM_ADMIN:  ["restricted", "confidential", "internal", "public"],
    Roles.AUDITOR:         ["restricted", "confidential", "internal", "public"],
    Roles.PROJECT_ADMIN:   ["confidential", "internal", "public"],
    Roles.DEPARTMENT_LEAD: ["confidential", "internal", "public"],
    Roles.EMPLOYEE:        ["internal", "public"],
}
_DEFAULT_CLEARANCE = ["internal", "public"]


def _get_clearance(user: User) -> list[str]:
    role_name = user.role.name if hasattr(user.role, "name") else str(user.role)
    return _CLEARANCE.get(role_name, _DEFAULT_CLEARANCE)


class IsolatedRetriever:
    """
    All methods enforce project-scoping as the *first* gate.
    Classification RBAC is applied *after* project-scoping.
    """

    # ------------------------------------------------------------------
    # Project-scoped vector search
    # ------------------------------------------------------------------

    def search(
        self,
        project_id: str,
        query: str,
        user: User,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Return top-k chunks from *this* project only.

        Steps:
        1. Embed query
        2. FAISS search with project_id namespace  → only that project's index
        3. Filter by user's classification clearance
        """
        if not project_id:
            raise ValueError("project_id is required for isolated search")

        query_vec = embedding_generator.get_embedding(query)
        # FAISS adapter already namespaces by project_id — cross-project impossible
        raw = vector_store.search(project_id, query_vec, top_k=top_k * 2)

        # Keyword Search Fallback:
        # Since local hash embeddings are pseudo-random, vector search scores can be low.
        # We load project metadata and calculate keyword overlap to boost retrieval accuracy.
        import pickle
        import os
        index_file, meta_file = vector_store._get_index_paths(project_id)
        metadata_list = []
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "rb") as f:
                    metadata_list = pickle.load(f)
            except Exception:
                pass

        query_words = [w.strip("?,.!:;()\"'") for w in query.lower().split()]
        query_words = [w for w in query_words if len(w) > 2] # ignore short words

        # Create a map of existing raw hits to check against
        raw_map = {hit["id"]: hit for hit in raw}

        if query_words and metadata_list:
            for chunk in metadata_list:
                text = chunk["text"].lower()
                matches = sum(1 for w in query_words if w in text)
                if matches > 0:
                    keyword_score = matches / len(query_words)
                    # Boost score to pass confidence threshold if there are strong keyword matches
                    if keyword_score >= 0.5:
                        keyword_score = max(keyword_score, 0.85)
                    
                    if chunk["id"] in raw_map:
                        raw_map[chunk["id"]]["score"] = max(raw_map[chunk["id"]]["score"], keyword_score)
                    else:
                        raw.append({
                            "id": chunk["id"],
                            "text": chunk["text"],
                            "score": keyword_score,
                            "metadata": chunk["metadata"]
                        })

        # Sort raw by score descending after keyword boost
        raw.sort(key=lambda x: x["score"], reverse=True)

        clearance = _get_clearance(user)
        results = []
        for hit in raw:
            doc_cls = hit.get("metadata", {}).get("classification", "internal").lower()
            if doc_cls in clearance:
                results.append(hit)
            if len(results) >= top_k:
                break

        logger.debug(
            "IsolatedRetriever.search project=%s user=%s raw=%d filtered=%d",
            project_id, user.id, len(raw), len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Single-chunk retrieval (DB-backed, no FAISS)
    # ------------------------------------------------------------------

    async def get_chunk(
        self,
        project_id: str,
        chunk_id: str,
        db: AsyncSession,
    ) -> Chunk:
        """
        Return a Chunk row only if it belongs to *project_id*.

        Raises 403 instead of 404 when the chunk exists but belongs to a
        different project — prevents enumeration attacks.
        """
        res = await db.execute(select(Chunk).where(Chunk.id == chunk_id))
        chunk = res.scalar_one_or_none()

        if not chunk:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

        if chunk.project_id != project_id:
            logger.warning(
                "IsolatedRetriever.get_chunk: cross-project access attempt "
                "chunk.project=%s caller.project=%s chunk_id=%s",
                chunk.project_id, project_id, chunk_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chunk does not belong to the specified project",
            )

        return chunk

    # ------------------------------------------------------------------
    # Global cross-project search (admin-only)
    # ------------------------------------------------------------------

    async def global_search(
        self,
        query: str,
        user: User,
        db: AsyncSession,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search across ALL projects.  Restricted to PLATFORM_ADMIN / AUDITOR.

        Iterates over every unique project_id in the DB (not the FAISS dir)
        and union-merges results, then sorts by score descending.
        """
        role_name = user.role.name if hasattr(user.role, "name") else str(user.role)
        if role_name not in (Roles.PLATFORM_ADMIN, Roles.AUDITOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global search is restricted to platform administrators and auditors",
            )

        from models.document import Document
        from sqlalchemy import distinct

        proj_res = await db.execute(
            select(distinct(Document.project_id)).where(Document.status == "ready")
        )
        project_ids = [row[0] for row in proj_res.all()]

        query_vec = embedding_generator.get_embedding(query)
        clearance = _get_clearance(user)

        all_hits: list[dict[str, Any]] = []
        for pid in project_ids:
            raw = vector_store.search(pid, query_vec, top_k=top_k)
            for hit in raw:
                if hit.get("metadata", {}).get("classification", "internal").lower() in clearance:
                    hit.setdefault("metadata", {})["project_id"] = pid
                    all_hits.append(hit)

        # Sort by score and take top_k
        all_hits.sort(key=lambda h: h.get("score", 0), reverse=True)
        return all_hits[:top_k]


isolated_retriever = IsolatedRetriever()
