from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_current_user, get_db
from app.schemas.job import (
    JobFetchResponse,
    JobListResponse,
    JobResponse,
    SavedJobListResponse,
    SavedJobResponse,
    SaveJobRequest,
)
from app.services import job as job_service

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


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


def _saved_job_response(saved_job: object, job: object) -> SavedJobResponse:
    """Build a SavedJobResponse from SavedJob + Job model instances."""
    return SavedJobResponse(
        id=str(saved_job.id),  # type: ignore[attr-defined]
        job=_job_response_from_model(job),
        saved_at=str(saved_job.saved_at),  # type: ignore[attr-defined]
        notes=saved_job.notes,  # type: ignore[attr-defined]
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/saved", response_model=SavedJobListResponse)
async def list_saved_jobs(
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SavedJobListResponse:
    """List all saved/bookmarked jobs for the authenticated user."""
    user_id = str(current_user["sub"])
    saved_rows = await job_service.get_saved_jobs(session, user_id)

    return SavedJobListResponse(
        saved_jobs=[_saved_job_response(sj, job) for sj, job in saved_rows],
        total=len(saved_rows),
    )


@router.get("", response_model=JobListResponse)
async def search_jobs(
    query: str = Query("", description="Search in title and company"),
    location: str | None = Query(None),
    salary_min: int | None = Query(None),
    salary_max: int | None = Query(None),
    job_type: str | None = Query(None),
    source: str | None = Query(None),
    is_remote: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """Search and list job listings with optional filters.

    This endpoint is publicly accessible (no authentication required).
    Supports filtering by text query, location, salary range, job type,
    source, and remote status. Results are paginated.
    """
    jobs, total = await job_service.search_jobs(
        session,
        query=query,
        location=location,
        salary_min=salary_min,
        salary_max=salary_max,
        job_type=job_type,
        source=source,
        is_remote=is_remote,
        page=page,
        page_size=page_size,
    )

    return JobListResponse(
        jobs=[_job_response_from_model(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Get detailed information about a single job listing.

    This endpoint is publicly accessible (no authentication required).
    """
    job = await job_service.get_job(session, job_id)
    return _job_response_from_model(job)


@router.post("/fetch", response_model=JobFetchResponse)
async def fetch_jobs(
    query: str = Query("software engineer", description="Search query for job APIs"),
    location: str | None = Query(None),
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JobFetchResponse:
    """Trigger a fetch of jobs from all configured external sources.

    Requires authentication. Fetches job listings from configured APIs
    (RemoteOK, The Muse, Adzuna, USAJobs) and upserts them into the database.
    """
    log.info(
        "job_fetch_triggered",
        user_id=str(current_user["sub"]),
        query=query,
        location=location,
    )

    results = await job_service.fetch_jobs_from_sources(
        session, query=query, location=location,
    )

    total_jobs = sum(results.values())
    return JobFetchResponse(
        sources_fetched=list(results.keys()),
        total_new_jobs=total_jobs,
        total_updated_jobs=0,
        message=f"Fetched {total_jobs} jobs from {len(results)} source(s)",
    )


@router.post("/{job_id}/save", response_model=SavedJobResponse, status_code=201)
async def save_job(
    job_id: str,
    body: SaveJobRequest | None = None,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SavedJobResponse:
    """Save/bookmark a job for the authenticated user.

    Optionally include notes about why this job is interesting.
    """
    user_id = str(current_user["sub"])
    notes = body.notes if body else None

    saved_job = await job_service.save_job(session, user_id, job_id, notes=notes)

    # Fetch the associated job for the response
    job = await job_service.get_job(session, job_id)
    return _saved_job_response(saved_job, job)


@router.delete("/{job_id}/save", status_code=204)
async def unsave_job(
    job_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Remove a saved/bookmarked job for the authenticated user."""
    user_id = str(current_user["sub"])
    await job_service.unsave_job(session, user_id, job_id)
    return Response(status_code=204)
