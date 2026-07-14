"""
Lexical reranking engine to refine vector similarity scores.
"""

from typing import Any, Dict, List


class Reranker:
    """
    Reranks chunks by combining dense semantic scores with lexical term matches
    to boost exact keyword matches (critical for codes, parts indices, and SOP numbers).
    """

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        query_tokens = set(query.lower().split())
        reranked = []

        for chunk in chunks:
            text = chunk["text"].lower()
            dense_score = chunk["score"]  # Dot product range [0, 1] typically
            
            # Simple lexical term match count
            lexical_matches = sum(1 for token in query_tokens if token in text)
            lexical_ratio = lexical_matches / max(1, len(query_tokens))
            
            # Composite Rerank Score: 70% semantic dense similarity, 30% lexical overlap
            composite_score = (dense_score * 0.7) + (lexical_ratio * 0.3)
            
            new_chunk = dict(chunk)
            new_chunk["score"] = composite_score
            reranked.append(new_chunk)

        # Sort descending by score
        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked[:top_n]


reranker = Reranker()
