"""
PDF text extractor.
"""
from pipeline.extractors import ExtractionError


def extract(file_path: str) -> str:
    """Extract text from a PDF file. Raises ExtractionError on failure."""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            raise ExtractionError("No PDF library available (install pypdf or PyPDF2)")

    try:
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        result = "\n".join(pages).strip()
        if not result:
            raise ExtractionError(f"PDF produced empty text: {file_path}")
        return result
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"PDF extraction failed for {file_path}: {exc}") from exc
