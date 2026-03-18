from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Public user representation returned in API responses."""

    id: str
    email: str
    full_name: str
    avatar_url: str | None
    auth_provider: str
    is_active: bool
    created_at: str
    updated_at: str


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Request body for email/password login."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response returned after successful registration or login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Response containing a new token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
