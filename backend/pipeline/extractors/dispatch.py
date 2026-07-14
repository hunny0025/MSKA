"""
Extractor dispatch table — routes file suffix to the correct extractor function.
"""
from pipeline.extractors import ExtractionError
from pipeline.extractors import (
    pdf_extractor,
    docx_extractor,
    xlsx_extractor,
    pptx_extractor,
    csv_extractor,
    txt_extractor,
)

_DISPATCH: dict = {
    ".pdf":  pdf_extractor.extract,
    ".docx": docx_extractor.extract,
    ".xlsx": xlsx_extractor.extract,
    ".xls":  xlsx_extractor.extract,
    ".pptx": pptx_extractor.extract,
    ".csv":  csv_extractor.extract,
    ".txt":  txt_extractor.extract,
}


def extract_text_from_file(file_path: str, suffix: str) -> str:
    """
    Dispatch extraction based on file suffix.

    Args:
        file_path: Absolute path to the file on disk.
        suffix: Lowercase file extension including the leading dot (e.g. '.pdf').

    Returns:
        Extracted plain-text string.

    Raises:
        ExtractionError: If suffix is unsupported or extraction fails.
    """
    extractor_fn = _DISPATCH.get(suffix.lower())
    if extractor_fn is None:
        raise ExtractionError(f"Unsupported file type: {suffix}")
    return extractor_fn(file_path)


SUPPORTED_SUFFIXES = list(_DISPATCH.keys())
