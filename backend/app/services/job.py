from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import or_
from sqlmodel import col, func, select

from app.config import get_settings
from app.exceptions import JobAlreadySavedError, JobFetchError, JobNotFoundError
from app.models.job import Job, SavedJob
from app.services.job_clients import (
    AdzunaClient,
    RemoteOKClient,
    TheMuseClient,
    USAJobsClient,
)

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

    from app.services.job_clients.base import NormalizedJob

log = structlog.get_logger()


async def search_jobs(
    session: AsyncSession,
    query: str = "",
    location: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    job_type: str | None = None,
    source: str | None = None,
    is_remote: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Job], int]:
    """Search for jobs with filtering and pagination.

    Builds a query with optional WHERE filters for title/company, location,
    salary range, job type, source, and remote status. Always filters for
    active jobs only.

    Args:
        session: Async database session.
        query: Free-text search against title and company (ILIKE).
        location: Location filter (ILIKE).
        salary_min: Minimum salary filter (job's max >= this value).
        salary_max: Maximum salary filter (job's min <= this value).
        job_type: Exact match on job type (e.g. "full-time").
        source: Exact match on job source (e.g. "remoteok").
        is_remote: If True, only return remote jobs.
        page: Page number (1-indexed).
        page_size: Number of results per page.

    Returns:
        Tuple of (list of Job models, total count).
    """
    # Build list of WHERE conditions
    conditions = [Job.is_active == True]  # noqa: E712

    if query:
        conditions.append(
            or_(
                col(Job.title).ilike(f"%{query}%"),
                col(Job.company).ilike(f"%{query}%"),
            )
        )

    if location:
        conditions.append(col(Job.location).ilike(f"%{location}%"))

    if salary_min is not None:
        conditions.append(col(Job.salary_max) >= salary_min)

    if salary_max is not None:
        conditions.append(col(Job.salary_min) <= salary_max)

    if job_type is not None:
        conditions.append(Job.job_type == job_type)

    if source is not None:
        conditions.append(Job.source == source)

    if is_remote is True:
        conditions.append(Job.is_remote == True)  # noqa: E712

    # Count total matching results
    count_statement = select(func.count()).select_from(Job).where(*conditions)
    count_result = await session.exec(count_statement)
    total: int = count_result.one()

    # Fetch paginated results ordered by newest first
    offset = (page - 1) * page_size
    jobs_statement = (
        select(Job)
        .where(*conditions)
        .order_by(col(Job.posted_at).desc())
        .offset(offset)
        .limit(page_size)
    )
    jobs_result = await session.exec(jobs_statement)
    jobs = list(jobs_result.all())

    log.info(
        "jobs_searched",
        query=query,
        location=location,
        total=total,
        page=page,
        page_size=page_size,
        returned=len(jobs),
    )
    return jobs, total


async def get_job(
    session: AsyncSession,
    job_id: str,
) -> Job:
    """Get a single job by its ID.

    Args:
        session: Async database session.
        job_id: UUID string of the job.

    Returns:
        The matching Job instance.

    Raises:
        JobNotFoundError: If no job exists with the given ID.
    """
    statement = select(Job).where(Job.id == uuid.UUID(job_id))
    result = await session.exec(statement)
    job = result.first()
    if job is None:
        log.warning("job_not_found", job_id=job_id)
        raise JobNotFoundError()
    return job


async def save_job(
    session: AsyncSession,
    user_id: str,
    job_id: str,
    notes: str | None = None,
) -> SavedJob:
    """Save/bookmark a job for a user.

    Args:
        session: Async database session.
        user_id: UUID string of the user.
        job_id: UUID string of the job to save.
        notes: Optional notes about the saved job.

    Returns:
        The newly created SavedJob instance.

    Raises:
        JobNotFoundError: If the job does not exist.
        JobAlreadySavedError: If the user has already saved this job.
    """
    # Verify the job exists
    await get_job(session, job_id)

    # Check not already saved
    existing_statement = select(SavedJob).where(
        SavedJob.user_id == uuid.UUID(user_id),
        SavedJob.job_id == uuid.UUID(job_id),
    )
    existing_result = await session.exec(existing_statement)
    if existing_result.first() is not None:
        log.warning("job_already_saved", user_id=user_id, job_id=job_id)
        raise JobAlreadySavedError()

    saved_job = SavedJob(
        user_id=uuid.UUID(user_id),
        job_id=uuid.UUID(job_id),
        notes=notes,
    )
    session.add(saved_job)
    await session.flush()

    log.info("job_saved", user_id=user_id, job_id=job_id)
    return saved_job


async def unsave_job(
    session: AsyncSession,
    user_id: str,
    job_id: str,
) -> None:
    """Remove a saved/bookmarked job for a user.

    Args:
        session: Async database session.
        user_id: UUID string of the user.
        job_id: UUID string of the job to unsave.

    Raises:
        JobNotFoundError: If no saved job entry is found.
    """
    statement = select(SavedJob).where(
        SavedJob.user_id == uuid.UUID(user_id),
        SavedJob.job_id == uuid.UUID(job_id),
    )
    result = await session.exec(statement)
    saved_job = result.first()
    if saved_job is None:
        log.warning("saved_job_not_found", user_id=user_id, job_id=job_id)
        raise JobNotFoundError(detail="Saved job not found")

    await session.delete(saved_job)
    await session.flush()

    log.info("job_unsaved", user_id=user_id, job_id=job_id)


async def get_saved_jobs(
    session: AsyncSession,
    user_id: str,
) -> list[tuple[SavedJob, Job]]:
    """Get all saved jobs for a user with their associated job data.

    Args:
        session: Async database session.
        user_id: UUID string of the user.

    Returns:
        List of (SavedJob, Job) tuples ordered by most recently saved first.
    """
    statement = (
        select(SavedJob, Job)
        .join(Job, SavedJob.job_id == Job.id)  # type: ignore[arg-type]
        .where(SavedJob.user_id == uuid.UUID(user_id))
        .order_by(col(SavedJob.saved_at).desc())
    )
    result = await session.exec(statement)
    rows = list(result.all())

    log.info("saved_jobs_listed", user_id=user_id, count=len(rows))
    return rows


def _parse_posted_at(posted_at_str: str | None) -> datetime | None:
    """Parse a posted_at ISO string into a datetime, returning None on failure.

    Args:
        posted_at_str: ISO format datetime string, or None.

    Returns:
        Parsed datetime with UTC timezone, or None.
    """
    if not posted_at_str:
        return None
    try:
        dt = datetime.fromisoformat(posted_at_str)
        # Ensure timezone-aware; assume UTC if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        log.warning("posted_at_parse_failed", value=posted_at_str)
        return None


def _apply_normalized_job_to_model(job: Job, nj: NormalizedJob) -> None:
    """Apply fields from a NormalizedJob dict onto a Job model instance.

    Args:
        job: The Job model to update.
        nj: The normalized job data from an API client.
    """
    job.title = nj["title"]
    job.company = nj["company"]
    job.location = nj["location"]
    job.is_remote = nj["is_remote"]
    job.salary_min = nj["salary_min"]
    job.salary_max = nj["salary_max"]
    job.salary_currency = nj["salary_currency"]
    job.description = nj["description"]
    job.job_type = nj["job_type"]
    job.url = nj["url"]
    job.tags = nj["tags"]
    job.raw_data = nj["raw_data"]
    job.posted_at = _parse_posted_at(nj["posted_at"])


async def fetch_jobs_from_sources(
    session: AsyncSession,
    query: str = "",
    location: str | None = None,
) -> dict[str, int]:
    """Fetch jobs from all configured external API sources and upsert into DB.

    Creates clients for each supported job board, fetches listings from those
    that are configured, and upserts each job into the database (matching on
    source + external_id).

    Args:
        session: Async database session.
        query: Search query to pass to job APIs.
        location: Location filter to pass to job APIs.

    Returns:
        Dict mapping source name to the number of jobs fetched from that source.

    Raises:
        JobFetchError: If all sources fail to return any results.
    """
    settings = get_settings()

    # Create all clients
    clients = [
        RemoteOKClient(),
        TheMuseClient(),
        AdzunaClient(
            app_id=settings.ADZUNA_APP_ID,
            app_key=settings.ADZUNA_APP_KEY,
        ),
        USAJobsClient(
            api_key=settings.USAJOBS_API_KEY,
            email=settings.USAJOBS_EMAIL,
        ),
    ]

    results: dict[str, int] = {}
    total_new = 0
    total_updated = 0

    for client in clients:
        if not client.is_configured():
            log.info("job_client_skipped", source=client.source_name, reason="not_configured")
            continue

        try:
            normalized_jobs = await client.fetch_jobs(
                query=query,
                location=location,
            )
        except Exception:
            log.exception("job_client_fetch_error", source=client.source_name)
            continue

        source_count = 0
        for nj in normalized_jobs:
            # Check for existing job by (source, external_id)
            existing_statement = select(Job).where(
                Job.source == nj["source"],
                Job.external_id == nj["external_id"],
            )
            existing_result = await session.exec(existing_statement)
            existing_job = existing_result.first()

            if existing_job:
                # Update existing job
                _apply_normalized_job_to_model(existing_job, nj)
                existing_job.updated_at = datetime.now(UTC)
                session.add(existing_job)
                total_updated += 1
            else:
                # Insert new job
                new_job = Job(
                    external_id=nj["external_id"],
                    source=nj["source"],
                    title=nj["title"],
                    company=nj["company"],
                    location=nj["location"],
                    is_remote=nj["is_remote"],
                    salary_min=nj["salary_min"],
                    salary_max=nj["salary_max"],
                    salary_currency=nj["salary_currency"],
                    description=nj["description"],
                    job_type=nj["job_type"],
                    url=nj["url"],
                    tags=nj["tags"],
                    raw_data=nj["raw_data"],
                    posted_at=_parse_posted_at(nj["posted_at"]),
                )
                session.add(new_job)
                total_new += 1

            source_count += 1

        await session.flush()
        results[client.source_name] = source_count

        log.info(
            "job_source_fetched",
            source=client.source_name,
            count=source_count,
        )

    if not results:
        log.warning("all_job_sources_failed", query=query, location=location)
        raise JobFetchError(detail="No job sources returned results")

    log.info(
        "jobs_fetch_complete",
        sources=list(results.keys()),
        total_new=total_new,
        total_updated=total_updated,
    )
    return results
