"""
Hand-rolled text chunker separating documents into semantic passages.
"""

from typing import List, Dict


class Chunker:
    """
    Splits long document text into overlapping windows.
    No LangChain dependency.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_text(self, text: str) -> List[str]:
        """
        Splits clean text into paragraphs or character-level overlapping windows.
        """
        if not text:
            return []

        # Clean whitespace
        normalized = " ".join(text.split())
        words = normalized.split(" ")
        
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i : i + self.chunk_size]
            chunks.append(" ".join(chunk_words))
            # Move index forward by chunk_size - overlap
            i += max(1, self.chunk_size - self.overlap)
            
        return chunks


chunker = Chunker()
