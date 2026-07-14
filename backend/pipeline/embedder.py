"""
A2 — Embedding generator (thin wrapper re-using the existing adapter).

Falls back to a deterministic hash-based vector when sentence-transformers
is not installed — identical to the original adapter's fallback logic.
"""
from adapters.ai.embeddings import embedding_generator


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Return a list of embedding vectors for *texts*.

    Delegates to the shared singleton EmbeddingGenerator in
    adapters.ai.embeddings so the sentence-transformer model is
    loaded at most once per process.
    """
    return embedding_generator.get_embeddings(texts)


def embed_text(text: str) -> list[float]:
    """Return a single embedding vector for *text*."""
    return embedding_generator.get_embedding(text)
