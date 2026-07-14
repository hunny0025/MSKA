"""
Custom exception for extractor failures.
"""


class ExtractionError(Exception):
    """Raised when a file extractor fails to produce text from a document."""
    pass
