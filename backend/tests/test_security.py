from __future__ import annotations

import time
from datetime import timedelta

import pytest

from app.exceptions import InvalidCredentialsError, TokenExpiredError
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Tests for hash_password() and verify_password()."""

    def test_hash_and_verify_password(self) -> None:
        plain = "my-secure-password"
        hashed = hash_password(plain)

        # Hash should differ from plaintext
        assert hashed != plain
        # Verification should succeed
        assert verify_password(plain, hashed) is True

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        """Each call should produce a different salt/hash."""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2  # bcrypt uses random salt


class TestJWT:
    """Tests for JWT token creation and decoding."""

    def test_create_and_decode_access_token(self) -> None:
        data = {"sub": "user-123"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_and_decode_refresh_token(self) -> None:
        data = {"sub": "user-456"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_expired_token_raises(self) -> None:
        data = {"sub": "user-789"}
        # Create a token that already expired 1 second ago
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(TokenExpiredError):
            decode_token(token)

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(InvalidCredentialsError):
            decode_token("this.is.not.a.valid.jwt")

    def test_access_token_contains_correct_type(self) -> None:
        token = create_access_token({"sub": "u1"})
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_contains_correct_type(self) -> None:
        token = create_refresh_token({"sub": "u2"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"
