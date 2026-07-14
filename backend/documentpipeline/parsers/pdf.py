"""
PDF document parser implementation with try-except fallback.
"""

from documentpipeline.parsers.base import BaseParser

try:
    import pypdf
except ImportError:
    pypdf = None


class PdfParser(BaseParser):
    """
    Parses PDF streams. Uses pypdf if available, otherwise runs fallback text extractor.
    """

    def extract_text(self, file_content: bytes) -> str:
        if pypdf:
            import io
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            text_parts = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
            return "\n".join(text_parts)
        
        # Fallback text finder from PDF streams (simple string decoder)
        import re
        text_blocks = re.findall(rb'\(.*?\) | \[.*?\]', file_content)
        cleaned = []
        for block in text_blocks:
            try:
                t = block.decode('ascii', errors='ignore').strip('()[] ')
                if len(t) > 2:
                    cleaned.append(t)
            except Exception:
                pass
        return " ".join(cleaned) if cleaned else "PDF parsed (binary text extraction fallback)"
