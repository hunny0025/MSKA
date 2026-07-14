"""
Text document parser implementation.
"""

from documentpipeline.parsers.base import BaseParser


class TxtParser(BaseParser):
    """
    Decodes raw text files.
    """

    def extract_text(self, file_content: bytes) -> str:
        return file_content.decode("utf-8", errors="ignore")
