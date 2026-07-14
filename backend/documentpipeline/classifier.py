"""
Metadata classification tag analyzer.
"""

import re


class DocumentClassifier:
    """
    Scans document content to verify or infer classification levels.
    """

    def __init__(self):
        self.keywords = {
            "restricted": re.compile(r"\b(?:restricted|proprietary|secret|trade secret)\b", re.IGNORECASE),
            "confidential": re.compile(r"\b(?:confidential|private|strictly confidential)\b", re.IGNORECASE),
            "internal": re.compile(r"\b(?:internal use|maruti suzuki internal)\b", re.IGNORECASE),
        }

    def infer_classification(self, text: str, user_provided: str = "internal") -> str:
        """
        Scans text for classification keywords and upgrades classifications if matched.
        """
        text_lower = text[:5000] # Check first 5000 chars (usually headers/footers contain labels)
        
        if self.keywords["restricted"].search(text_lower):
            return "restricted"
        if self.keywords["confidential"].search(text_lower):
            # Upgrades 'public' or 'internal' to 'confidential'
            if user_provided in ("public", "internal"):
                return "confidential"
        if self.keywords["internal"].search(text_lower):
            if user_provided == "public":
                return "internal"
                
        return user_provided


classifier = DocumentClassifier()
