from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from sqlmodel import select

from app.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.models.user import User, UserProfile
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()


def _issue_tokens(user: User) -> tuple[str, str]:
    """Create an access/refresh token pair for the given user."""
    data: dict[str, str | int] = {"sub": str(user.id)}
    return create_access_token(data), create_refresh_token(data)


async def register_user(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str,
) -> tuple[User, str, str]:
    """Register a new user with email/password.

    Creates User + empty UserProfile.
    Returns (user, access_token, refresh_token).
    Raises DuplicateEmailError if email exists.
    """
    existing = await get_user_by_email(session, email)
    if existing is not None:
        log.warning("registration_duplicate_email", email=email)
        raise DuplicateEmailError()

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        auth_provider="email",
    )
    session.add(user)
    await session.flush()

    profile = UserProfile(user_id=user.id)
    session.add(profile)
    await session.flush()

    log.info("user_registered", user_id=str(user.id), email=email)

    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    """Authenticate user with email/password.

    Returns (user, access_token, refresh_token).
    Raises InvalidCredentialsError if email/password wrong.
    """
    user = await get_user_by_email(session, email)
    if user is None:
        log.warning("auth_failed_unknown_email", email=email)
        raise InvalidCredentialsError()

    if user.hashed_password is None or not verify_password(password, user.hashed_password):
        log.warning("auth_failed_bad_password", user_id=str(user.id))
        raise InvalidCredentialsError()

    log.info("user_authenticated", user_id=str(user.id))

    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token


async def get_user_by_id(
    session: AsyncSession,
    user_id: str,
) -> User:
    """Get user by ID. Raises UserNotFoundError if not found."""
    statement = select(User).where(User.id == uuid.UUID(user_id))
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        log.warning("user_not_found", user_id=user_id)
        raise UserNotFoundError()
    return user


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """Get user by email. Returns None if not found."""
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()


async def handle_oauth_user(
    session: AsyncSession,
    email: str,
    full_name: str,
    avatar_url: str | None,
    auth_provider: str,
    auth_provider_id: str,
) -> tuple[User, str, str]:
    """Handle OAuth login/registration.

    If user exists with this email, log them in (issue tokens).
    If new email, create user + empty profile.
    Returns (user, access_token, refresh_token).
    """
    user = await get_user_by_email(session, email)

    if user is not None:
        log.info("oauth_login_existing_user", user_id=str(user.id), provider=auth_provider)
        access_token, refresh_token = _issue_tokens(user)
        return user, access_token, refresh_token

    user = User(
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        auth_provider=auth_provider,
        auth_provider_id=auth_provider_id,
    )
    session.add(user)
    await session.flush()

    profile = UserProfile(user_id=user.id)
    session.add(profile)
    await session.flush()

    log.info("oauth_user_registered", user_id=str(user.id), provider=auth_provider)

    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token


async def refresh_tokens(
    session: AsyncSession,
    refresh_token: str,
) -> tuple[str, str]:
    """Validate refresh token and issue new token pair.

    Returns (new_access_token, new_refresh_token).
    Raises TokenExpiredError or InvalidCredentialsError.
    """
    payload = decode_token(refresh_token)

    token_type = payload.get("type")
    if token_type != "refresh":
        log.warning("refresh_token_wrong_type", token_type=token_type)
        raise InvalidCredentialsError(detail="Invalid token type")

    sub = payload.get("sub")
    if sub is None:
        log.warning("refresh_token_missing_sub")
        raise InvalidCredentialsError(detail="Invalid token payload")

    user = await get_user_by_id(session, str(sub))

    log.info("tokens_refreshed", user_id=str(user.id))

    return _issue_tokens(user)
