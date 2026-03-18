from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import Request


class AppException(Exception):  # noqa: N818
    """Base application exception with structured error details."""

    def __init__(
        self,
        detail: str,
        error_code: str,
        status_code: int = 400,
    ) -> None:
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(detail)


class UserNotFoundError(AppException):
    """Raised when a requested user does not exist."""

    def __init__(self, detail: str = "User not found") -> None:
        super().__init__(
            detail=detail,
            error_code="USER_NOT_FOUND",
            status_code=404,
        )


class DuplicateEmailError(AppException):
    """Raised when attempting to register with an existing email."""

    def __init__(self, detail: str = "A user with this email already exists") -> None:
        super().__init__(
            detail=detail,
            error_code="DUPLICATE_EMAIL",
            status_code=409,
        )


class InvalidCredentialsError(AppException):
    """Raised when authentication credentials are invalid."""

    def __init__(self, detail: str = "Invalid email or password") -> None:
        super().__init__(
            detail=detail,
            error_code="INVALID_CREDENTIALS",
            status_code=401,
        )


class TokenExpiredError(AppException):
    """Raised when a JWT token has expired."""

    def __init__(self, detail: str = "Token has expired") -> None:
        super().__init__(
            detail=detail,
            error_code="TOKEN_EXPIRED",
            status_code=401,
        )


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    """Global exception handler that converts AppException into a structured JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "detail": exc.detail,
            },
        },
    )
