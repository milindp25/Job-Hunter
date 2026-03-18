from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.config import Settings, get_settings
from app.dependencies import get_db
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    handle_oauth_user,
    refresh_tokens,
    register_user,
)

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# OAuth provider configuration
# ---------------------------------------------------------------------------

_GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
_GOOGLE_SCOPES = "openid email profile"

_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
_GITHUB_SCOPES = "read:user user:email"

_LINKEDIN_AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
_LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
_LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
_LINKEDIN_SCOPES = "openid profile email"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_response_from_model(user: object) -> UserResponse:
    """Build a UserResponse from a User SQLModel instance."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        auth_provider=user.auth_provider,
        is_active=user.is_active,
        created_at=str(user.created_at),
        updated_at=str(user.updated_at),
    )


def _set_refresh_cookie(
    response: Response,
    refresh_token: str,
    settings: Settings,
) -> None:
    """Set the refresh token as an httpOnly cookie on the response."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


# ---------------------------------------------------------------------------
# Email / password endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    """Register a new user with email and password."""
    user, access_token, refresh_token = await register_user(
        session,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )

    _set_refresh_cookie(response, refresh_token, settings)

    return AuthResponse(
        access_token=access_token,
        user=_user_response_from_model(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    """Authenticate with email and password."""
    user, access_token, refresh_token = await authenticate_user(
        session,
        email=body.email,
        password=body.password,
    )

    _set_refresh_cookie(response, refresh_token, settings)

    return AuthResponse(
        access_token=access_token,
        user=_user_response_from_model(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Exchange a refresh token for a new access/refresh token pair."""
    access_token, new_refresh_token = await refresh_tokens(
        session,
        refresh_token=body.refresh_token,
    )

    _set_refresh_cookie(response, new_refresh_token, settings)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Log out by clearing the refresh token cookie."""
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------


@router.get("/google")
async def google_login(
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Redirect the user to Google's OAuth consent screen."""
    client = AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=f"{settings.BACKEND_URL}/api/v1/auth/google/callback",
        scope=_GOOGLE_SCOPES,
    )
    authorization_url, _state = client.create_authorization_url(
        _GOOGLE_AUTHORIZE_URL,
    )
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Handle the callback from Google OAuth, issue tokens, and redirect."""
    client = AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=f"{settings.BACKEND_URL}/api/v1/auth/google/callback",
    )

    code = request.query_params.get("code", "")
    await client.fetch_token(
        _GOOGLE_TOKEN_URL,
        code=code,
    )

    resp = await client.get(_GOOGLE_USERINFO_URL)
    user_info: dict[str, str] = resp.json()

    email = user_info.get("email", "")
    full_name = user_info.get("name", "")
    avatar_url = user_info.get("picture")
    provider_id = user_info.get("id", "")

    user, access_token, refresh_token = await handle_oauth_user(
        session,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        auth_provider="google",
        auth_provider_id=provider_id,
    )

    redirect_url = f"{settings.FRONTEND_URL}?access_token={access_token}"
    response = RedirectResponse(url=redirect_url)
    _set_refresh_cookie(response, refresh_token, settings)
    return response


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------


@router.get("/github")
async def github_login(
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Redirect the user to GitHub's OAuth consent screen."""
    client = AsyncOAuth2Client(
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        redirect_uri=f"{settings.BACKEND_URL}/api/v1/auth/github/callback",
        scope=_GITHUB_SCOPES,
    )
    authorization_url, _state = client.create_authorization_url(
        _GITHUB_AUTHORIZE_URL,
    )
    return RedirectResponse(url=authorization_url)


@router.get("/github/callback")
async def github_callback(
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Handle the callback from GitHub OAuth, issue tokens, and redirect."""
    client = AsyncOAuth2Client(
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        redirect_uri=f"{settings.BACKEND_URL}/api/v1/auth/github/callback",
    )

    code = request.query_params.get("code", "")
    await client.fetch_token(
        _GITHUB_TOKEN_URL,
        code=code,
    )

    # Fetch user profile
    user_resp = await client.get(
        _GITHUB_USER_URL,
        headers={"Accept": "application/json"},
    )
    user_info: dict[str, str | int | None] = user_resp.json()

    # GitHub may not expose email publicly; fetch from emails endpoint
    email = str(user_info.get("email") or "")
    if not email:
        emails_resp = await client.get(
            _GITHUB_EMAILS_URL,
            headers={"Accept": "application/json"},
        )
        emails: list[dict[str, str | bool]] = emails_resp.json()
        for entry in emails:
            if entry.get("primary") and entry.get("verified"):
                email = str(entry.get("email", ""))
                break

    full_name = str(user_info.get("name") or user_info.get("login") or "")
    avatar_url = str(user_info.get("avatar_url") or "") or None
    provider_id = str(user_info.get("id", ""))

    user, access_token, refresh_token = await handle_oauth_user(
        session,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        auth_provider="github",
        auth_provider_id=provider_id,
    )

    redirect_url = f"{settings.FRONTEND_URL}?access_token={access_token}"
    response = RedirectResponse(url=redirect_url)
    _set_refresh_cookie(response, refresh_token, settings)
    return response


# ---------------------------------------------------------------------------
# LinkedIn OAuth
# ---------------------------------------------------------------------------


@router.get("/linkedin")
async def linkedin_login(
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Redirect the user to LinkedIn's OAuth consent screen."""
    client = AsyncOAuth2Client(
        client_id=settings.LINKEDIN_CLIENT_ID,
        client_secret=settings.LINKEDIN_CLIENT_SECRET,
        redirect_uri=f"{settings.BACKEND_URL}/api/v1/auth/linkedin/callback",
        scope=_LINKEDIN_SCOPES,
    )
    authorization_url, _state = client.create_authorization_url(
        _LINKEDIN_AUTHORIZE_URL,
    )
    return RedirectResponse(url=authorization_url)


@router.get("/linkedin/callback")
async def linkedin_callback(
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Handle the callback from LinkedIn OAuth, issue tokens, and redirect."""
    client = AsyncOAuth2Client(
        client_id=settings.LINKEDIN_CLIENT_ID,
        client_secret=settings.LINKEDIN_CLIENT_SECRET,
        redirect_uri=f"{settings.BACKEND_URL}/api/v1/auth/linkedin/callback",
    )

    code = request.query_params.get("code", "")
    await client.fetch_token(
        _LINKEDIN_TOKEN_URL,
        code=code,
    )

    resp = await client.get(_LINKEDIN_USERINFO_URL)
    user_info: dict[str, str] = resp.json()

    email = user_info.get("email", "")
    full_name = user_info.get("name", "")
    avatar_url = user_info.get("picture")
    provider_id = user_info.get("sub", "")

    user, access_token, refresh_token = await handle_oauth_user(
        session,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        auth_provider="linkedin",
        auth_provider_id=provider_id,
    )

    redirect_url = f"{settings.FRONTEND_URL}?access_token={access_token}"
    response = RedirectResponse(url=redirect_url)
    _set_refresh_cookie(response, refresh_token, settings)
    return response
