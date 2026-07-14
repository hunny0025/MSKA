"""
Confidence calculator for retrieval verification.
"""

from typing import Any, Dict, List
from core.config import get_settings

settings = get_settings()


class ConfidenceEngine:
    """
    Evaluates whether retrieved chunks satisfy confidence thresholds.
    Triggers answer abstention ("I don't know") if retrieval matches are weak.
    """

    def __init__(self):
        self.threshold = settings.rag_confidence_threshold

    def calculate_confidence(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Derives query confidence score based on top reranked similarities.
        
        Returns:
            Dict containing:
            - "score": computed float [0, 1]
            - "should_abstain": bool (True if score < threshold)
        """
        if not chunks:
            return {"score": 0.0, "should_abstain": True}

        # Best chunk similarity acts as primary indicator
        best_score = chunks[0]["score"]
        
        # Normalize/clamp score to [0, 1] range
        normalized_score = max(0.0, min(1.0, best_score))
        
        should_abstain = normalized_score < self.threshold
        
        return {
            "score": normalized_score,
            "should_abstain": should_abstain
        }


confidence_engine = ConfidenceEngine()
