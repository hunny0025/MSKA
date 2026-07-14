"""
Search logic layer executing semantic and metadata-filtered queries.
"""

from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.document import Document
from models.user import User
from rag.retriever import retriever
from rag.relationships import relationship_analyzer


class SearchService:
    """
    Handles database metadata lookup and coordinates semantic retrieval.
    Enforces user classification clearance gates.
    """

    async def execute_hybrid_search(
        self,
        db: AsyncSession,
        query: str | None,
        project_id: str | None,
        classification_filter: str | None,
        user: User
    ) -> List[Dict[str, Any]]:
        # 1. Fetch user clearance list (reuse retriever gate)
        clearance_list = retriever._get_classification_clearance(user.role.name)

        # 2. Build SQL query for document metadata
        sql_query = select(Document)
        
        # Apply filters
        if project_id:
            sql_query = sql_query.where(Document.project_id == project_id)
        if classification_filter:
            # Check requested filter is within user's clearance boundary
            if classification_filter.lower() in clearance_list:
                sql_query = sql_query.where(Document.classification == classification_filter.lower())
            else:
                return [] # Requesting tags higher than clearance returns empty
        else:
            # Enforce global clearance constraint mapping
            sql_query = sql_query.where(Document.classification.in_(clearance_list))

        # We only retrieve approved documents
        sql_query = sql_query.where(Document.status == "approved")

        result = await db.execute(sql_query)
        raw_docs = list(result.scalars().all())
        
        # Defense-in-depth: enforce classification checks in code
        all_matched_docs = [
            d for d in raw_docs 
            if d.classification.lower() in clearance_list
        ]


        if not query:
            # Return metadata results directly if no semantic query is present
            return [
                {
                    "document": {
                        "id": d.id,
                        "filename": d.filename,
                        "classification": d.classification,
                        "version": d.version,
                        "project_id": d.project_id
                    },
                    "relationships": relationship_analyzer.analyze_relationships(d, all_matched_docs),
                    "search_score": 1.0
                } for d in all_matched_docs
            ]

        # 3. Handle Semantic Query
        # Retrieve matching chunks (already permission-filtered internally by retriever)
        proj_scope = project_id or "global_placeholder"
        semantic_chunks = retriever.retrieve_relevant_chunks(proj_scope, query, user, top_k=20)
        
        # Extract document IDs from chunks
        doc_chunk_map = {}
        for chunk in semantic_chunks:
            doc_id = chunk["metadata"].get("document_id")
            if doc_id:
                doc_chunk_map.setdefault(doc_id, []).append(chunk)

        # Map document details for chunks
        search_results = []
        for doc in all_matched_docs:
            if doc.id in doc_chunk_map:
                chunks = doc_chunk_map[doc.id]
                # Best chunk score determines document relevance rank
                best_score = max([c["score"] for c in chunks])
                
                search_results.append({
                    "document": {
                        "id": doc.id,
                        "filename": doc.filename,
                        "classification": doc.classification,
                        "version": doc.version,
                        "project_id": doc.project_id
                    },
                    "matches": [
                        {"chunk_id": c["id"], "text": c["text"], "score": c["score"]} 
                        for c in chunks
                    ],
                    "relationships": relationship_analyzer.analyze_relationships(doc, all_matched_docs),
                    "search_score": best_score
                })

        # Sort results by best matching score
        search_results.sort(key=lambda x: x["search_score"], reverse=True)
        return search_results


search_service = SearchService()
