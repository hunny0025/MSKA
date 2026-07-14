"""
Shared state between E2E test modules and conftest hooks.
"""

# Dict populated by test_verification_checks.py, read by conftest.py's
# pytest_sessionfinish hook to generate the verification report.
VERIFICATION_RESULTS = {}
