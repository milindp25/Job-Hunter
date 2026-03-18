from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.exceptions import InvalidCredentialsError, TokenExpiredError

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt with 12 rounds."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, str | int], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to encode in the token (must include "sub").
        expires_delta: Custom expiration duration. Defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": int(expire.timestamp()), "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=_ALGORITHM)


def create_refresh_token(data: dict[str, str | int]) -> str:
    """Create a signed JWT refresh token with extended expiry.

    Args:
        data: Claims to encode in the token (must include "sub").

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": int(expire.timestamp()), "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, str | int]:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded token payload.

    Raises:
        TokenExpiredError: If the token has expired.
        InvalidCredentialsError: If the token is malformed or invalid.
    """
    try:
        payload: dict[str, str | int] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[_ALGORITHM],
        )
    except JWTError as exc:
        error_message = str(exc).lower()
        if "expired" in error_message:
            raise TokenExpiredError from exc
        raise InvalidCredentialsError(detail="Could not validate token") from exc

    return payload
