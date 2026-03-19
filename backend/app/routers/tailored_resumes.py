from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Response

from app.dependencies import get_current_user, get_db
from app.schemas.tailored_resume import (
    TailoredResumeListResponse,
    TailoredResumeResponse,
    TailorResumeRequest,
)
from app.services.resume_tailor import ResumeTailorService

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/tailored-resumes", tags=["tailored-resumes"])

_service = ResumeTailorService()


def _to_response(tailored: object) -> TailoredResumeResponse:
    """Convert a TailoredResume model to a response schema."""
    return TailoredResumeResponse(
        id=str(tailored.id),  # type: ignore[attr-defined]
        resume_id=str(tailored.resume_id),  # type: ignore[attr-defined]
        job_id=str(tailored.job_id),  # type: ignore[attr-defined]
        tailored_summary=tailored.tailored_summary,  # type: ignore[attr-defined]
        tailored_experience=tailored.tailored_experience,  # type: ignore[attr-defined]
        tailored_skills=tailored.tailored_skills,  # type: ignore[attr-defined]
        keyword_matches=tailored.keyword_matches,  # type: ignore[attr-defined]
        keyword_gaps=tailored.keyword_gaps,  # type: ignore[attr-defined]
        match_score_before=tailored.match_score_before,  # type: ignore[attr-defined]
        match_score_after=tailored.match_score_after,  # type: ignore[attr-defined]
        ai_model=tailored.ai_model,  # type: ignore[attr-defined]
        created_at=str(tailored.created_at),  # type: ignore[attr-defined]
    )


@router.post("/", response_model=TailoredResumeResponse, status_code=201)
async def create_tailored_resume(
    body: TailorResumeRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TailoredResumeResponse:
    """Tailor a resume for a specific job using AI."""
    user_id = str(current_user["sub"])
    tailored = await _service.tailor_resume(
        session,
        user_id=user_id,
        resume_id=body.resume_id,
        job_id=body.job_id,
    )
    return _to_response(tailored)


@router.get("/", response_model=TailoredResumeListResponse)
async def list_tailored_resumes(
    resume_id: str | None = None,
    job_id: str | None = None,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TailoredResumeListResponse:
    """List tailored resumes for the authenticated user."""
    user_id = str(current_user["sub"])
    items = await _service.list_tailored_resumes(
        session,
        user_id=user_id,
        resume_id=resume_id,
        job_id=job_id,
    )
    return TailoredResumeListResponse(
        items=[_to_response(item) for item in items],
        total=len(items),
    )


@router.get("/{tailored_id}", response_model=TailoredResumeResponse)
async def get_tailored_resume(
    tailored_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TailoredResumeResponse:
    """Get a specific tailored resume by ID."""
    user_id = str(current_user["sub"])
    tailored = await _service.get_tailored_resume(session, user_id, tailored_id)
    return _to_response(tailored)


@router.delete("/{tailored_id}", status_code=204)
async def delete_tailored_resume(
    tailored_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a tailored resume."""
    user_id = str(current_user["sub"])
    await _service.delete_tailored_resume(session, user_id, tailored_id)
    return Response(status_code=204)
