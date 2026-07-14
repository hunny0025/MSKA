"""
Rule/Regex-based PII scanning scanner.
"""

import re


class PIIScanner:
    """
    Flags personal details (Aadhaar cards, PAN card numbers, phone numbers, emails)
    to quarantine sensitive employee data from public indices.
    """

    def __init__(self):
        # Compiled patterns
        self.patterns = {
            "email": re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"),
            # Indian mobile numbers: e.g. +91 9876543210 or 98765-43210 or 09876543210
            "phone": re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b|\b\d{5}[-\s]?\d{5}\b"),
            # Aadhaar: 12 digits with spaces or hyphens
            "aadhaar": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            # PAN Card: 5 letters, 4 numbers, 1 letter
            "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
            # General salary/CTC pattern
            "salary": re.compile(r"\b(?:ctc|salary|stipend|compensation)\b.*?\b\d+[\d,]*\b", re.IGNORECASE)
        }

    def scan(self, text: str) -> dict:
        """
        Scans text and returns mapping of detected patterns and boolean flagged status.
        """
        results = {}
        flagged = False
        
        for key, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                flagged = True
                results[key] = len(matches)
                
        return {"flagged": flagged, "matches": results}


pii_scanner = PIIScanner()
