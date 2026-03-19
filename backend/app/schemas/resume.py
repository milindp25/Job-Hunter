from __future__ import annotations

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    """Single resume representation."""

    id: str
    user_id: str
    filename: str
    file_size: int
    file_type: str
    is_primary: bool
    parsed_data: dict[str, str | None | list[str] | list[dict[str, str | None]]]
    created_at: str
    updated_at: str


class ResumeListResponse(BaseModel):
    """List of resumes for a user."""

    resumes: list[ResumeResponse]
    total: int


class ResumeDownloadResponse(BaseModel):
    """Presigned download URL response."""

    download_url: str
    filename: str
    expires_in: int


class ResumeUploadResponse(BaseModel):
    """Response after successful resume upload."""

    resume: ResumeResponse
    message: str
