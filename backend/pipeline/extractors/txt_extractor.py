"""
TXT text extractor.
"""
from pipeline.extractors import ExtractionError


def extract(file_path: str) -> str:
    """Extract text from a plain text file. Raises ExtractionError on failure."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            result = f.read().strip()
        if not result:
            raise ExtractionError(f"TXT file is empty: {file_path}")
        return result
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"TXT extraction failed for {file_path}: {exc}") from exc
