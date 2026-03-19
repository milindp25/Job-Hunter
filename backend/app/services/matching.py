from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlmodel import col, func, select

from app.exceptions import (
    GeminiAnalysisError,
    JobNotFoundError,
    MatchNotFoundError,
    ProfileIncompleteError,
)
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.user import UserProfile
from app.services import gemini as gemini_service
from app.services.keyword_matcher import calculate_keyword_match

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_user_profile_for_matching(
    session: AsyncSession,
    user_id: str,
) -> UserProfile:
    """Load user profile and validate it has enough data for matching.

    Args:
        session: Async database session.
        user_id: UUID string of the user.

    Returns:
        The user's profile.

    Raises:
        ProfileIncompleteError: If the profile has no skills.
    """
    statement = select(UserProfile).where(
        UserProfile.user_id == uuid.UUID(user_id),
    )
    result = await session.exec(statement)
    profile = result.first()

    if profile is None or not profile.skills:
        log.warning("profile_incomplete_for_matching", user_id=user_id)
        raise ProfileIncompleteError()

    return profile


async def _get_primary_resume(
    session: AsyncSession,
    user_id: str,
) -> Resume | None:
    """Get the user's primary resume, or most recent if no primary is set.

    Args:
        session: Async database session.
        user_id: UUID string of the user.

    Returns:
        The primary (or most recent) Resume, or None if no resumes exist.
    """
    # Try primary first
    primary_stmt = select(Resume).where(
        Resume.user_id == uuid.UUID(user_id),
        Resume.is_primary == True,  # noqa: E712
    )
    primary_result = await session.exec(primary_stmt)
    primary = primary_result.first()
    if primary is not None:
        return primary

    # Fall back to most recent
    recent_stmt = (
        select(Resume)
        .where(Resume.user_id == uuid.UUID(user_id))
        .order_by(col(Resume.created_at).desc())
        .limit(1)
    )
    recent_result = await session.exec(recent_stmt)
    return recent_result.first()


def _calculate_overall_score(keyword_score: int, ai_score: int | None) -> int:
    """Calculate blended overall score from keyword and AI scores.

    If no AI score is available, the keyword score is used directly.
    When both are present, the AI score is weighted at 70% and keyword at 30%.

    Args:
        keyword_score: Layer 1 keyword-based score (0-100).
        ai_score: Layer 2 Gemini-based score (0-100), or None.

    Returns:
        Blended overall score (0-100).
    """
    if ai_score is None:
        return keyword_score
    return round(keyword_score * 0.3 + ai_score * 0.7)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_bulk_matching(
    session: AsyncSession,
    user_id: str,
    min_keyword_score: int = 20,
) -> dict[str, int]:
    """Run Layer 1 keyword matching against all active jobs.

    Loads the user profile, iterates over every active job, computes a
    keyword match score, and upserts a JobMatch record for jobs that score
    above the minimum threshold.

    Args:
        session: Async database session.
        user_id: UUID string of the user.
        min_keyword_score: Minimum keyword score to create/keep a match.

    Returns:
        Dict with keys: total_jobs_analyzed, new_matches, updated_matches,
        top_score.

    Raises:
        ProfileIncompleteError: If user profile lacks skills.
    """
    profile = await _get_user_profile_for_matching(session, user_id)

    # Fetch all active jobs
    jobs_stmt = select(Job).where(col(Job.is_active) == True)  # noqa: E712
    jobs_result = await session.exec(jobs_stmt)
    all_jobs = list(jobs_result.all())

    log.info(
        "bulk_matching_started",
        user_id=user_id,
        total_active_jobs=len(all_jobs),
        min_keyword_score=min_keyword_score,
    )

    new_matches = 0
    updated_matches = 0
    top_score = 0
    user_uuid = uuid.UUID(user_id)

    for job in all_jobs:
        # Run Layer 1 keyword matching
        kw_result = calculate_keyword_match(
            user_skills=profile.skills,
            user_desired_roles=profile.desired_roles,
            user_desired_locations=profile.desired_locations,
            user_min_salary=profile.min_salary,
            user_years_of_experience=profile.years_of_experience,
            job_title=job.title,
            job_description=job.description,
            job_tags=job.tags,
            job_location=job.location,
            job_is_remote=job.is_remote,
            job_salary_min=job.salary_min,
            job_salary_max=job.salary_max,
        )

        # Skip low-scoring jobs
        if kw_result.overall_score < min_keyword_score:
            continue

        # Check if a match already exists for this user + job
        existing_stmt = select(JobMatch).where(
            JobMatch.user_id == user_uuid,
            JobMatch.job_id == job.id,
        )
        existing_result = await session.exec(existing_stmt)
        existing_match = existing_result.first()

        if existing_match is not None:
            # Update existing match with new keyword score
            existing_match.keyword_score = kw_result.overall_score
            existing_match.overall_score = _calculate_overall_score(
                kw_result.overall_score,
                existing_match.ai_score,
            )
            existing_match.updated_at = datetime.now(UTC)
            session.add(existing_match)
            updated_matches += 1
            top_score = max(top_score, existing_match.overall_score)
        else:
            # Create new match
            new_match = JobMatch(
                user_id=user_uuid,
                job_id=job.id,
                keyword_score=kw_result.overall_score,
                overall_score=kw_result.overall_score,
            )
            session.add(new_match)
            new_matches += 1
            top_score = max(top_score, kw_result.overall_score)

    await session.flush()

    log.info(
        "bulk_matching_complete",
        user_id=user_id,
        total_jobs_analyzed=len(all_jobs),
        new_matches=new_matches,
        updated_matches=updated_matches,
        top_score=top_score,
    )

    return {
        "total_jobs_analyzed": len(all_jobs),
        "new_matches": new_matches,
        "updated_matches": updated_matches,
        "top_score": top_score,
    }


async def analyze_single_match(
    session: AsyncSession,
    user_id: str,
    job_id: str,
) -> JobMatch:
    """Perform deep analysis on a single job using keyword + Gemini AI.

    If a recent (< 7 days) AI-scored match already exists, it is returned
    without re-analysis. Otherwise, keyword matching is run first, then
    Gemini AI analysis is attempted if configured.

    Args:
        session: Async database session.
        user_id: UUID string of the user.
        job_id: UUID string of the job.

    Returns:
        The upserted JobMatch with AI scores (if Gemini is available).

    Raises:
        ProfileIncompleteError: If user profile lacks skills.
        JobNotFoundError: If the job does not exist.
        GeminiAnalysisError: If Gemini analysis fails unexpectedly.
    """
    profile = await _get_user_profile_for_matching(session, user_id)
    resume = await _get_primary_resume(session, user_id)

    # Load the job
    job_stmt = select(Job).where(Job.id == uuid.UUID(job_id))
    job_result = await session.exec(job_stmt)
    job = job_result.first()
    if job is None:
        log.warning("job_not_found_for_matching", job_id=job_id)
        raise JobNotFoundError()

    user_uuid = uuid.UUID(user_id)

    # Check for existing fresh AI-scored match
    existing_stmt = select(JobMatch).where(
        JobMatch.user_id == user_uuid,
        JobMatch.job_id == job.id,
    )
    existing_result = await session.exec(existing_stmt)
    existing_match = existing_result.first()

    freshness_cutoff = datetime.now(UTC) - timedelta(days=7)

    if (
        existing_match is not None
        and existing_match.ai_score is not None
        and existing_match.updated_at > freshness_cutoff
    ):
        log.info(
            "match_cache_hit",
            user_id=user_id,
            job_id=job_id,
            overall_score=existing_match.overall_score,
        )
        return existing_match

    # Run keyword matching to get/create the base match
    kw_result = calculate_keyword_match(
        user_skills=profile.skills,
        user_desired_roles=profile.desired_roles,
        user_desired_locations=profile.desired_locations,
        user_min_salary=profile.min_salary,
        user_years_of_experience=profile.years_of_experience,
        job_title=job.title,
        job_description=job.description,
        job_tags=job.tags,
        job_location=job.location,
        job_is_remote=job.is_remote,
        job_salary_min=job.salary_min,
        job_salary_max=job.salary_max,
    )

    if existing_match is None:
        # Create a new match record
        existing_match = JobMatch(
            user_id=user_uuid,
            job_id=job.id,
            keyword_score=kw_result.overall_score,
            overall_score=kw_result.overall_score,
        )
        session.add(existing_match)
        await session.flush()
    else:
        # Update keyword score on existing match
        existing_match.keyword_score = kw_result.overall_score
        existing_match.updated_at = datetime.now(UTC)

    # Attempt Gemini AI analysis if configured
    if gemini_service.is_gemini_configured():
        try:
            resume_text = resume.raw_text if resume else ""
            profile_summary = profile.summary or ""

            ai_result = await gemini_service.analyze_job_match(
                profile_summary=profile_summary,
                resume_text=resume_text,
                job_title=job.title,
                job_company=job.company,
                job_description=job.description,
                job_tags=job.tags,
                job_location=job.location,
                job_is_remote=job.is_remote,
                job_salary_min=job.salary_min,
                job_salary_max=job.salary_max,
                user_desired_roles=profile.desired_roles,
                user_desired_locations=profile.desired_locations,
                user_min_salary=profile.min_salary,
                user_years_of_experience=profile.years_of_experience,
            )

            # Update match with AI scores
            existing_match.ai_score = ai_result.overall_score
            existing_match.skills_match = ai_result.skills_match
            existing_match.experience_match = ai_result.experience_match
            existing_match.education_match = ai_result.education_match
            existing_match.location_match = ai_result.location_match
            existing_match.salary_match = ai_result.salary_match
            existing_match.strengths = ai_result.strengths
            existing_match.gaps = ai_result.gaps
            existing_match.recommendation = ai_result.recommendation
            existing_match.overall_score = _calculate_overall_score(
                kw_result.overall_score,
                ai_result.overall_score,
            )
            existing_match.updated_at = datetime.now(UTC)

            log.info(
                "single_match_ai_complete",
                user_id=user_id,
                job_id=job_id,
                keyword_score=kw_result.overall_score,
                ai_score=ai_result.overall_score,
                overall_score=existing_match.overall_score,
            )

        except GeminiAnalysisError:
            log.warning(
                "gemini_analysis_failed_fallback_keyword",
                user_id=user_id,
                job_id=job_id,
            )
            # Keep keyword-only scores; do not re-raise
    else:
        log.info(
            "single_match_keyword_only",
            user_id=user_id,
            job_id=job_id,
            keyword_score=kw_result.overall_score,
        )

    session.add(existing_match)
    await session.flush()

    return existing_match


async def get_match_results(
    session: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    min_score: int = 0,
) -> tuple[list[tuple[JobMatch, Job]], int]:
    """Get paginated match results for a user, ordered by score descending.

    Args:
        session: Async database session.
        user_id: UUID string of the user.
        page: Page number (1-indexed).
        page_size: Number of results per page.
        min_score: Minimum overall_score filter.

    Returns:
        Tuple of (list of (JobMatch, Job) pairs, total count).
    """
    user_uuid = uuid.UUID(user_id)

    # Count total matching results
    count_stmt = (
        select(func.count())
        .select_from(JobMatch)
        .where(
            JobMatch.user_id == user_uuid,
            JobMatch.overall_score >= min_score,
        )
    )
    count_result = await session.exec(count_stmt)
    total: int = count_result.one()

    # Fetch paginated matches
    match_stmt = (
        select(JobMatch)
        .where(
            JobMatch.user_id == user_uuid,
            JobMatch.overall_score >= min_score,
        )
        .order_by(col(JobMatch.overall_score).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    match_result = await session.exec(match_stmt)
    matches = list(match_result.all())

    # Fetch corresponding jobs for each match
    pairs: list[tuple[JobMatch, Job]] = []
    for match in matches:
        job_stmt = select(Job).where(Job.id == match.job_id)
        job_result = await session.exec(job_stmt)
        job = job_result.first()
        if job:
            pairs.append((match, job))

    log.info(
        "match_results_fetched",
        user_id=user_id,
        total=total,
        page=page,
        page_size=page_size,
        returned=len(pairs),
    )

    return pairs, total


async def get_match_detail(
    session: AsyncSession,
    user_id: str,
    job_id: str,
) -> tuple[JobMatch, Job]:
    """Get a single match detail with its associated job.

    Args:
        session: Async database session.
        user_id: UUID string of the user.
        job_id: UUID string of the job.

    Returns:
        Tuple of (JobMatch, Job).

    Raises:
        MatchNotFoundError: If no match exists for the user + job.
        JobNotFoundError: If the associated job no longer exists.
    """
    user_uuid = uuid.UUID(user_id)

    match_stmt = select(JobMatch).where(
        JobMatch.user_id == user_uuid,
        JobMatch.job_id == uuid.UUID(job_id),
    )
    match_result = await session.exec(match_stmt)
    match = match_result.first()

    if match is None:
        log.warning("match_not_found", user_id=user_id, job_id=job_id)
        raise MatchNotFoundError()

    job_stmt = select(Job).where(Job.id == uuid.UUID(job_id))
    job_result = await session.exec(job_stmt)
    job = job_result.first()

    if job is None:
        log.warning("job_not_found_for_match", user_id=user_id, job_id=job_id)
        raise JobNotFoundError()

    return match, job
