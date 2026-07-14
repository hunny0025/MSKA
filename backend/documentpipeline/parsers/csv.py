"""
CSV document parser implementation.
"""

from documentpipeline.parsers.base import BaseParser


class CsvParser(BaseParser):
    """
    Decodes CSV files, returns them clean.
    """

    def extract_text(self, file_content: bytes) -> str:
        return file_content.decode("utf-8", errors="ignore")
