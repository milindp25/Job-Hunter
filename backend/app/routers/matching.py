from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_db
from app.schemas.job import JobResponse
from app.schemas.matching import (
    JobMatchResponse,
    JobMatchWithJobResponse,
    MatchAnalyzeResponse,
    MatchResultsResponse,
    SingleMatchAnalyzeResponse,
)
from app.services import matching as matching_service

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _job_response_from_model(job: object) -> JobResponse:
    """Build a JobResponse from a Job SQLModel instance."""
    return JobResponse(
        id=str(job.id),  # type: ignore[attr-defined]
        external_id=job.external_id,  # type: ignore[attr-defined]
        source=job.source,  # type: ignore[attr-defined]
        title=job.title,  # type: ignore[attr-defined]
        company=job.company,  # type: ignore[attr-defined]
        location=job.location,  # type: ignore[attr-defined]
        is_remote=job.is_remote,  # type: ignore[attr-defined]
        salary_min=job.salary_min,  # type: ignore[attr-defined]
        salary_max=job.salary_max,  # type: ignore[attr-defined]
        salary_currency=job.salary_currency,  # type: ignore[attr-defined]
        description=job.description,  # type: ignore[attr-defined]
        job_type=job.job_type,  # type: ignore[attr-defined]
        url=job.url,  # type: ignore[attr-defined]
        tags=job.tags,  # type: ignore[attr-defined]
        posted_at=str(job.posted_at) if job.posted_at else None,  # type: ignore[attr-defined]
        is_active=job.is_active,  # type: ignore[attr-defined]
        created_at=str(job.created_at),  # type: ignore[attr-defined]
        updated_at=str(job.updated_at),  # type: ignore[attr-defined]
    )


def _match_response_from_model(match: object) -> JobMatchResponse:
    """Build a JobMatchResponse from a JobMatch SQLModel instance."""
    return JobMatchResponse(
        id=str(match.id),  # type: ignore[attr-defined]
        job_id=str(match.job_id),  # type: ignore[attr-defined]
        overall_score=match.overall_score,  # type: ignore[attr-defined]
        keyword_score=match.keyword_score,  # type: ignore[attr-defined]
        ai_score=match.ai_score,  # type: ignore[attr-defined]
        skills_match=match.skills_match,  # type: ignore[attr-defined]
        experience_match=match.experience_match,  # type: ignore[attr-defined]
        education_match=match.education_match,  # type: ignore[attr-defined]
        location_match=match.location_match,  # type: ignore[attr-defined]
        salary_match=match.salary_match,  # type: ignore[attr-defined]
        strengths=match.strengths,  # type: ignore[attr-defined]
        gaps=match.gaps,  # type: ignore[attr-defined]
        recommendation=match.recommendation,  # type: ignore[attr-defined]
        created_at=str(match.created_at),  # type: ignore[attr-defined]
        updated_at=str(match.updated_at),  # type: ignore[attr-defined]
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=MatchAnalyzeResponse)
async def analyze_matches(
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MatchAnalyzeResponse:
    """Run bulk keyword matching for the authenticated user.

    Analyzes all active jobs against the user's profile and resume,
    creating or updating match records for jobs that meet the minimum
    keyword score threshold.
    """
    user_id = str(current_user["sub"])
    log.info("bulk_matching_requested", user_id=user_id)

    result = await matching_service.run_bulk_matching(session, user_id)

    return MatchAnalyzeResponse(
        total_jobs_analyzed=result["total_jobs_analyzed"],
        new_matches=result["new_matches"],
        updated_matches=result["updated_matches"],
        top_score=result["top_score"],
        message=(
            f"Analyzed {result['total_jobs_analyzed']} jobs. "
            f"{result['new_matches']} new matches, "
            f"{result['updated_matches']} updated."
        ),
    )


@router.get("/results", response_model=MatchResultsResponse)
async def get_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_score: int = Query(0, ge=0, le=100),
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MatchResultsResponse:
    """Get paginated match results for the authenticated user.

    Returns matches sorted by overall score in descending order.
    Supports filtering by minimum score and pagination.
    """
    user_id = str(current_user["sub"])

    pairs, total = await matching_service.get_match_results(
        session,
        user_id,
        page=page,
        page_size=page_size,
        min_score=min_score,
    )

    matches = [
        JobMatchWithJobResponse(
            match=_match_response_from_model(match),
            job=_job_response_from_model(job),
        )
        for match, job in pairs
    ]

    return MatchResultsResponse(
        matches=matches,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/results/{job_id}", response_model=JobMatchWithJobResponse)
async def get_match_detail(
    job_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JobMatchWithJobResponse:
    """Get detailed match information for a specific job.

    Returns the match scores and analysis alongside the full job data
    for the authenticated user.
    """
    user_id = str(current_user["sub"])

    match, job = await matching_service.get_match_detail(
        session, user_id, job_id,
    )

    return JobMatchWithJobResponse(
        match=_match_response_from_model(match),
        job=_job_response_from_model(job),
    )


@router.post("/analyze/{job_id}", response_model=SingleMatchAnalyzeResponse)
async def analyze_single_match(
    job_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SingleMatchAnalyzeResponse:
    """Run deep analysis on a single job using keyword + Gemini AI.

    Performs keyword matching first, then attempts Gemini AI analysis
    if configured. Returns detailed scoring breakdown including skills,
    experience, education, location, and salary match scores.
    """
    user_id = str(current_user["sub"])
    log.info("single_match_analysis_requested", user_id=user_id, job_id=job_id)

    match = await matching_service.analyze_single_match(
        session, user_id, job_id,
    )

    ai_label = "AI-enhanced" if match.ai_score is not None else "keyword-only"

    return SingleMatchAnalyzeResponse(
        match=_match_response_from_model(match),
        message=f"Analysis complete ({ai_label}). Overall score: {match.overall_score}/100.",
    )
