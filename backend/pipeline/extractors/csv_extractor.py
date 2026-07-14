"""
CSV text extractor.
"""
import csv
from pipeline.extractors import ExtractionError


def extract(file_path: str) -> str:
    """Extract text from a .csv file as readable rows. Raises ExtractionError on failure."""
    try:
        parts = []
        with open(file_path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                row_text = " | ".join(cell.strip() for cell in row if cell.strip())
                if row_text:
                    parts.append(row_text)
        result = "\n".join(parts).strip()
        if not result:
            raise ExtractionError(f"CSV produced empty text: {file_path}")
        return result
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"CSV extraction failed for {file_path}: {exc}") from exc
