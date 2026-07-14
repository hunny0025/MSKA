"""
Unit tests for core security utilities (password hashing + JWT).
"""

import pytest
from datetime import timedelta
from unittest.mock import patch
from jose import JWTError


# Patch settings before importing security module
@pytest.fixture(autouse=True)
def mock_settings():
    """Provide test settings without needing a real .env file."""
    mock = type("Settings", (), {
        "jwt_secret_key": "test-secret-key-for-unit-tests-only",
        "jwt_algorithm": "HS256",
        "jwt_access_token_expire_minutes": 30,
        "jwt_refresh_token_expire_days": 7,
    })()
    with patch("core.security.get_settings", return_value=mock):
        yield mock


class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_password_returns_hash(self):
        """Hashing produces a non-empty string different from the input."""
        from core.security import hash_password
        hashed = hash_password("mypassword123")
        assert hashed
        assert hashed != "mypassword123"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        """Correct password verifies successfully."""
        from core.security import hash_password, verify_password
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_verify_wrong_password(self):
        """Wrong password fails verification."""
        from core.security import hash_password, verify_password
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Same password produces different hashes (salt is working)."""
        from core.security import hash_password
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2


class TestJWT:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        """Access token is a non-empty string."""
        from core.security import create_access_token
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Access token decodes back to original payload."""
        from core.security import create_access_token, decode_token
        token = create_access_token({"sub": "user-456", "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "user-456"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Refresh token has 'refresh' type claim."""
        from core.security import create_refresh_token, decode_token
        token = create_refresh_token({"sub": "user-789"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_verify_token_type_access(self):
        """verify_token_type accepts matching type."""
        from core.security import create_access_token, verify_token_type
        token = create_access_token({"sub": "user-1"})
        payload = verify_token_type(token, "access")
        assert payload["sub"] == "user-1"

    def test_verify_token_type_mismatch(self):
        """verify_token_type rejects wrong type."""
        from core.security import create_access_token, verify_token_type
        token = create_access_token({"sub": "user-1"})
        with pytest.raises(JWTError):
            verify_token_type(token, "refresh")

    def test_expired_token_raises(self):
        """Expired token raises JWTError on decode."""
        from core.security import create_access_token, decode_token
        token = create_access_token(
            {"sub": "user-1"},
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(JWTError):
            decode_token(token)

    def test_tampered_token_raises(self):
        """Tampered token raises JWTError."""
        from core.security import create_access_token, decode_token
        token = create_access_token({"sub": "user-1"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_custom_expiry(self):
        """Custom expiry delta is respected."""
        from core.security import create_access_token, decode_token
        token = create_access_token(
            {"sub": "user-1"},
            expires_delta=timedelta(hours=2),
        )
        payload = decode_token(token)
        assert payload["sub"] == "user-1"
