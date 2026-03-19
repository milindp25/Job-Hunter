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


class ResumeNotFoundError(AppException):
    """Raised when a requested resume does not exist."""

    def __init__(self, detail: str = "Resume not found") -> None:
        super().__init__(detail=detail, error_code="RESUME_NOT_FOUND", status_code=404)


class ResumeUploadError(AppException):
    """Raised when resume upload/storage fails."""

    def __init__(self, detail: str = "Failed to upload resume") -> None:
        super().__init__(detail=detail, error_code="RESUME_UPLOAD_ERROR", status_code=500)


class ResumeLimitExceededError(AppException):
    """Raised when user exceeds the maximum number of stored resumes."""

    def __init__(self, detail: str = "Maximum resume limit reached (10)") -> None:
        super().__init__(detail=detail, error_code="RESUME_LIMIT_EXCEEDED", status_code=400)


class InvalidFileTypeError(AppException):
    """Raised when an unsupported file type is uploaded."""

    def __init__(self, detail: str = "Only PDF and DOCX files are accepted") -> None:
        super().__init__(detail=detail, error_code="INVALID_FILE_TYPE", status_code=400)


class FileTooLargeError(AppException):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, detail: str = "File too large. Maximum size is 5 MB") -> None:
        super().__init__(detail=detail, error_code="FILE_TOO_LARGE", status_code=400)


class JobNotFoundError(AppException):
    """Raised when a requested job does not exist."""

    def __init__(self, detail: str = "Job not found") -> None:
        super().__init__(detail=detail, error_code="JOB_NOT_FOUND", status_code=404)


class JobAlreadySavedError(AppException):
    """Raised when a user tries to save a job they already saved."""

    def __init__(self, detail: str = "Job is already saved") -> None:
        super().__init__(detail=detail, error_code="JOB_ALREADY_SAVED", status_code=409)


class JobFetchError(AppException):
    """Raised when fetching jobs from an external API fails."""

    def __init__(self, detail: str = "Failed to fetch jobs from external source") -> None:
        super().__init__(detail=detail, error_code="JOB_FETCH_ERROR", status_code=500)


class GeminiAnalysisError(AppException):
    """Raised when Gemini AI analysis fails."""

    def __init__(self, detail: str = "AI analysis failed") -> None:
        super().__init__(detail=detail, error_code="GEMINI_ANALYSIS_ERROR", status_code=500)


class MatchNotFoundError(AppException):
    """Raised when a requested match result does not exist."""

    def __init__(self, detail: str = "Match result not found") -> None:
        super().__init__(detail=detail, error_code="MATCH_NOT_FOUND", status_code=404)


class ProfileIncompleteError(AppException):
    """Raised when user profile is too incomplete for matching."""

    def __init__(
        self,
        detail: str = "Profile is too incomplete for matching. Please add skills and experience.",
    ) -> None:
        super().__init__(detail=detail, error_code="PROFILE_INCOMPLETE", status_code=400)


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
