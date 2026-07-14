"""
Unit tests for document processing pipeline (parsers, PII scanning, classifier).
"""

import pytest

from documentpipeline.parsers.registry import parser_registry
from documentpipeline.pii_scanner import pii_scanner
from documentpipeline.classifier import classifier


def test_txt_parser():
    """Text parser should return decodable utf-8 contents."""
    parser = parser_registry.get_parser(".txt")
    raw = b"Maruti Suzuki Baleno manual details."
    text = parser.extract_text(raw)
    assert text == "Maruti Suzuki Baleno manual details."


def test_pii_scanner_clean():
    """Clean text should not trigger PII flag."""
    text = "This is a clean document detailing standard procedures for wheel balancing."
    res = pii_scanner.scan(text)
    assert res["flagged"] is False


def test_pii_scanner_flagged_email():
    """Text containing email should trigger PII warning."""
    text = "For queries contact HR representative at ramesh.sharma@marutisuzuki.com."
    res = pii_scanner.scan(text)
    assert res["flagged"] is True
    assert "email" in res["matches"]


def test_pii_scanner_flagged_aadhaar():
    """Aadhaar pattern should trigger quarantine flag."""
    text = "Employee record ID copy: Aadhaar Card Number 1234 5678 9012"
    res = pii_scanner.scan(text)
    assert res["flagged"] is True
    assert "aadhaar" in res["matches"]


def test_pii_scanner_flagged_pan():
    """PAN Card pattern triggers quarantine flag."""
    text = "PAN Card detail: ABCDE1234F"
    res = pii_scanner.scan(text)
    assert res["flagged"] is True
    assert "pan" in res["matches"]


def test_classifier_verify_upgrade():
    """Document containing confidential label triggers classification upgrade."""
    text = "This is a strictly confidential document containing vehicle safety designs."
    inferred = classifier.infer_classification(text, user_provided="public")
    assert inferred == "confidential"


def test_classifier_restricted_upgrade():
    """Restricted keyword overrides user provided internal label."""
    text = "Proprietary powertrain schematics. This trade secret is restricted."
    inferred = classifier.infer_classification(text, user_provided="internal")
    assert inferred == "restricted"
