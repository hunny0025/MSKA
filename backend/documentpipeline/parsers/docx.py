"""
DOCX document parser implementation using standard library zipfile + ElementTree.
"""

import io
import zipfile
import xml.etree.ElementTree as ET

from documentpipeline.parsers.base import BaseParser


class DocxParser(BaseParser):
    """
    Parses Office DOCX streams without external dependencies.
    """

    def extract_text(self, file_content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as docx:
                # Text is stored in word/document.xml
                xml_content = docx.read('word/document.xml')
                root = ET.fromstring(xml_content)
                
                # Namespace mapping
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                
                # Find all text elements <w:t>
                text_elements = root.findall('.//w:t', ns)
                text = [el.text for el in text_elements if el.text]
                return " ".join(text)
        except Exception as e:
            return f"DOCX Parse Error: {str(e)}"
