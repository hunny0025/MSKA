"""
Abstract Base Document Parser class.
"""

from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    Interface for extracting raw text from specialized file streams.
    """

    @abstractmethod
    def extract_text(self, file_content: bytes) -> str:
        """
        Parses binary file contents and returns a clean string.
        """
        pass
