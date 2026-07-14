"""
XLSX document parser implementation using standard library zipfile + ElementTree.
"""

import io
import zipfile
import xml.etree.ElementTree as ET

from documentpipeline.parsers.base import BaseParser


class XlsxParser(BaseParser):
    """
    Parses Office XLSX streams without external dependencies.
    """

    def extract_text(self, file_content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as xlsx:
                # Text in Excel is gathered in sharedStrings.xml
                try:
                    xml_content = xlsx.read('xl/sharedStrings.xml')
                except KeyError:
                    # No shared strings (empty workbook or numbers-only)
                    return "Empty XLSX or Numeric-only sheet"
                
                root = ET.fromstring(xml_content)
                # Text elements are usually <t> tags (namespace prefix varies, we can use universal matching)
                text = [el.text for el in root.iter() if el.tag.endswith('t') and el.text]
                return " ".join(text)
        except Exception as e:
            return f"XLSX Parse Error: {str(e)}"
