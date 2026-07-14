"""
A2 — PII Scanner (pure-Python regex, no DB knowledge).

Returns PIIScanResult — never logs the matched string content, only the pattern type.
"""
import re
from dataclasses import dataclass, field


_PATTERNS: dict[str, re.Pattern] = {
    "aadhaar": re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "pan":     re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "email":   re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"),
    "phone":   re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}\b|\b\d{5}[\s\-]\d{5}\b"),
}


@dataclass
class PIIScanResult:
    """Result of PII scanning.  matched_types lists pattern labels, never raw PII strings."""
    has_pii: bool
    matched_types: list[str] = field(default_factory=list)


def scan(text: str) -> PIIScanResult:
    """
    Scan *text* for PII patterns.

    Returns a PIIScanResult where matched_types contains pattern labels
    (e.g. ["aadhaar", "email"]) but never the actual matched text.
    """
    matched_types: list[str] = []
    for label, pattern in _PATTERNS.items():
        if pattern.search(text):
            matched_types.append(label)
    return PIIScanResult(has_pii=bool(matched_types), matched_types=matched_types)
