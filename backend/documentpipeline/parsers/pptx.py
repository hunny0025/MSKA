"""
PPTX document parser implementation using standard library zipfile + ElementTree.
"""

import io
import zipfile
import xml.etree.ElementTree as ET

from documentpipeline.parsers.base import BaseParser


class PptxParser(BaseParser):
    """
    Parses Office PPTX streams without external dependencies.
    """

    def extract_text(self, file_content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as pptx:
                text_parts = []
                # Slides are ppt/slides/slide1.xml, slide2.xml, etc.
                slide_files = [name for name in pptx.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml')]
                
                # Sort slide files numerically
                slide_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))
                
                ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
                
                for slide_name in slide_files:
                    xml_content = pptx.read(slide_name)
                    root = ET.fromstring(xml_content)
                    # Find all text elements <a:t>
                    text_elements = root.findall('.//a:t', ns)
                    slide_text = [el.text for el in text_elements if el.text]
                    if slide_text:
                        text_parts.append(" ".join(slide_text))
                        
                return "\n\n".join(text_parts)
        except Exception as e:
            return f"PPTX Parse Error: {str(e)}"
