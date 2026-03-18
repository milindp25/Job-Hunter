from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db as _get_db
from app.exceptions import InvalidCredentialsError
from app.utils.security import decode_token

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

# Re-export get_db for convenient imports from dependencies module
get_db = _get_db

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    """Extract and validate the current user from the Authorization header.

    Reads the Bearer token, decodes it, and returns the token payload
    containing user claims (e.g. "sub" with the user ID).

    Args:
        credentials: Bearer token extracted from the Authorization header.
        session: Async database session (available for user lookups if needed).

    Returns:
        Decoded JWT payload dictionary with user claims.

    Raises:
        InvalidCredentialsError: If no token is provided or the token is invalid.
        TokenExpiredError: If the token has expired.
    """
    if credentials is None:
        raise InvalidCredentialsError(detail="Authentication required")

    payload = decode_token(credentials.credentials)

    token_type = payload.get("type")
    if token_type != "access":
        raise InvalidCredentialsError(detail="Invalid token type: expected access token")

    sub = payload.get("sub")
    if sub is None:
        raise InvalidCredentialsError(detail="Token missing subject claim")

    return payload
