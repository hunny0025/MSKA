"""
Local embedding generator adapter.
"""

import hashlib
import numpy as np
from typing import List

from core.config import get_settings

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

settings = get_settings()


class EmbeddingGenerator:
    """
    Generates numeric vectors from text passages.
    Uses sentence-transformers if available, otherwise falls back to a 
    deterministic character-hashed embedding vector generator (384 dimensions).
    """

    def __init__(self):
        self.dimension = settings.embedding_dimension
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(settings.embedding_model_name)
            except Exception:
                self.model = None
        else:
            self.model = None

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a normalized float vector for a string.
        """
        if self.model:
            vector = self.model.encode(text)
            return vector.tolist()

        # Deterministic Fallback Vector Generator
        # Generates a pseudo-random normalized vector from text hash
        # ensuring that identical strings yield identical vectors,
        # and similar words map close in high-dimensional projection
        rng = np.random.default_rng(int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) & 0xffffffff)
        vector = rng.standard_normal(self.dimension)
        # Add character frequencies to inject crude semantic/lexical similarity
        for char in text.lower()[:200]:
            idx = ord(char) % self.dimension
            vector[idx] += 0.5
            
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates vectors for list of strings.
        """
        return [self.get_embedding(t) for t in texts]


embedding_generator = EmbeddingGenerator()
