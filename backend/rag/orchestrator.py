"""
RAG Orchestrator binding retrieval, reranking, and confidence verification.
"""

from typing import Any, Dict, List
from models.user import User
from rag.retriever import retriever
from rag.reranker import reranker
from rag.confidence import confidence_engine
from adapters.ai.factory import ai_provider


class RAGOrchestrator:
    """
    Coordinates RAG phases: retrieves, reranks, checks confidence, and generates response via AI provider.
    """

    async def execute_query(
        self, 
        project_id: str, 
        query: str, 
        user: User
    ) -> Dict[str, Any]:
        """
        Executes query retrieval pipeline and validates confidence metrics.
        """
        # 1. Retrieve Candidate Chunks
        raw_chunks = retriever.retrieve_relevant_chunks(project_id, query, user)
        
        # 2. Rerank Chunks
        reranked_chunks = reranker.rerank(query, raw_chunks)
        
        # 3. Assess Confidence
        conf_report = confidence_engine.calculate_confidence(reranked_chunks)
        
        # 4. Generate Answer via AI provider
        # Enforce cost control: short-circuit immediately without calling AI Provider on low confidence
        if conf_report["should_abstain"]:
            answer = "I do not have enough verified information to answer your request."
        else:
            answer = await ai_provider.generate_response(query, reranked_chunks)

        return {
            "answer": answer,
            "confidence_score": conf_report["score"],
            "should_abstain": conf_report["should_abstain"],
            "citations": [
                {
                    "document_id": chunk["metadata"].get("document_id"),
                    "filename": chunk["metadata"].get("filename"),
                    "chunk_id": chunk["id"],
                    "text": chunk["text"]
                } for chunk in reranked_chunks
            ] if not conf_report["should_abstain"] else []
        }


rag_orchestrator = RAGOrchestrator()

