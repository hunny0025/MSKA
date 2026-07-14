"""
A2 — Sliding-window text chunker (pure Python, no external deps).

Default: 512-char chunks, 64-char overlap.
"""


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """
    Split *text* into overlapping character-level windows.

    Args:
        text:       Plain-text string to chunk.
        chunk_size: Maximum characters per chunk (default 512).
        overlap:    Number of characters shared between consecutive chunks (default 64).

    Returns:
        List of chunk strings; empty list if text is blank.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += step
    return chunks
