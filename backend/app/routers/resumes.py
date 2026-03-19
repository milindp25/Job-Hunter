from __future__ import annotations

import uuid as _uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Response, UploadFile

from app.dependencies import get_current_user, get_db
from app.schemas.resume import (
    ResumeDownloadResponse,
    ResumeListResponse,
    ResumeResponse,
    ResumeUploadResponse,
)
from app.services import resume as resume_service
from app.services.resume_generator import ResumeGeneratorService
from app.services.resume_templates import TemplateRegistry

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])

_generator = ResumeGeneratorService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resume_response_from_model(resume: object) -> ResumeResponse:
    """Convert a Resume model instance to a ResumeResponse schema."""
    return ResumeResponse(
        id=str(resume.id),  # type: ignore[attr-defined]
        user_id=str(resume.user_id),  # type: ignore[attr-defined]
        filename=resume.filename,  # type: ignore[attr-defined]
        file_size=resume.file_size,  # type: ignore[attr-defined]
        file_type=resume.file_type,  # type: ignore[attr-defined]
        is_primary=resume.is_primary,  # type: ignore[attr-defined]
        parsed_data=resume.parsed_data,  # type: ignore[attr-defined]
        created_at=str(resume.created_at),  # type: ignore[attr-defined]
        updated_at=str(resume.updated_at),  # type: ignore[attr-defined]
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=ResumeUploadResponse)
async def upload_resume_endpoint(
    file: UploadFile,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResumeUploadResponse:
    """Upload a resume file (PDF or DOCX)."""
    user_id = str(current_user["sub"])
    content = await file.read()

    resume = await resume_service.upload_resume(
        session, user_id, content, file.filename or "unknown",
    )

    return ResumeUploadResponse(
        resume=_resume_response_from_model(resume),
        message="Resume uploaded successfully",
    )


@router.get("", response_model=ResumeListResponse)
async def list_resumes_endpoint(
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResumeListResponse:
    """List all resumes for the authenticated user."""
    user_id = str(current_user["sub"])
    resumes = await resume_service.get_resumes(session, user_id)

    return ResumeListResponse(
        resumes=[_resume_response_from_model(r) for r in resumes],
        total=len(resumes),
    )


@router.get("/templates")
async def list_resume_templates() -> dict[str, list[dict[str, str]]]:
    """List available resume PDF templates."""
    templates = TemplateRegistry.list_templates()
    return {"templates": templates}


@router.get("/{resume_id}/generate")
async def generate_resume_pdf(
    resume_id: str,
    template: str = "classic",
    accent_color: str | None = None,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Generate a PDF resume from stored resume data."""
    user_id = _uuid.UUID(str(current_user["sub"]))
    rid = _uuid.UUID(resume_id)

    pdf_bytes = await _generator.generate_pdf(
        session=session,
        user_id=user_id,
        resume_id=rid,
        template_id=template,
        accent_color=accent_color,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="resume_{resume_id}_{template}.pdf"',
        },
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume_endpoint(
    resume_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Get a single resume by ID."""
    user_id = str(current_user["sub"])
    resume = await resume_service.get_resume(session, user_id, resume_id)

    return _resume_response_from_model(resume)


@router.get("/{resume_id}/download", response_model=ResumeDownloadResponse)
async def download_resume_endpoint(
    resume_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResumeDownloadResponse:
    """Generate a presigned download URL for a resume."""
    user_id = str(current_user["sub"])
    resume = await resume_service.get_resume(session, user_id, resume_id)
    download_url = await resume_service.get_resume_download_url(resume)

    return ResumeDownloadResponse(
        download_url=download_url,
        filename=resume.filename,
        expires_in=3600,
    )


@router.delete("/{resume_id}", status_code=204)
async def delete_resume_endpoint(
    resume_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a resume by ID."""
    user_id = str(current_user["sub"])
    await resume_service.delete_resume(session, user_id, resume_id)

    return Response(status_code=204)


@router.put("/{resume_id}/primary", response_model=ResumeResponse)
async def set_primary_resume_endpoint(
    resume_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Set a resume as the user's primary resume."""
    user_id = str(current_user["sub"])
    resume = await resume_service.set_primary_resume(session, user_id, resume_id)

    return _resume_response_from_model(resume)
