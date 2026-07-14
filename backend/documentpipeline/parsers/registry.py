"""
Document parser registry mapping extensions to specialized parser classes.
"""

from typing import Dict
from documentpipeline.parsers.base import BaseParser
from documentpipeline.parsers.pdf import PdfParser
from documentpipeline.parsers.docx import DocxParser
from documentpipeline.parsers.xlsx import XlsxParser
from documentpipeline.parsers.pptx import PptxParser
from documentpipeline.parsers.txt import TxtParser
from documentpipeline.parsers.csv import CsvParser


class ParserRegistry:
    """
    Lookup registry mapping file extensions to parser handlers.
    """

    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {
            ".pdf": PdfParser(),
            ".docx": DocxParser(),
            ".xlsx": XlsxParser(),
            ".pptx": PptxParser(),
            ".txt": TxtParser(),
            ".csv": CsvParser(),
        }

    def get_parser(self, extension: str) -> BaseParser:
        """
        Retrieves matching parser or raises ValueError.
        """
        ext = extension.lower().strip()
        if not ext.startswith("."):
            ext = "." + ext

        parser = self._parsers.get(ext)
        if not parser:
            raise ValueError(f"Unsupported file extension: '{extension}'")
        return parser


# Singleton instance
parser_registry = ParserRegistry()
