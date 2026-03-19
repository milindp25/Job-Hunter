"""ATS Compliance Checker orchestrator service.

Coordinates format-rule checking (ats_rules) and optional Gemini AI analysis
to produce an AtsCheck record per (resume, job) combination.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlmodel import col, func, select

from app.exceptions import (
    AtsCheckNotFoundError,
    AtsConsentRequiredError,
    AtsRateLimitError,
    GeminiAnalysisError,
    JobNotFoundError,
    ResumeNotFoundError,
)
from app.models.ats_check import AtsCheck
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import UserProfile
from app.services import ats_rules
from app.services import gemini as gemini_service

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RATE_LIMIT_FULL_CHECKS_PER_HOUR = 10
PROMPT_VERSION = "v1"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _check_rate_limit(session: AsyncSession, user_uuid: uuid.UUID) -> None:
    """Raise AtsRateLimitError if the user has hit the hourly full-check cap.

    Args:
        session: Async database session.
        user_uuid: UUID of the user.

    Raises:
        AtsRateLimitError: If >= RATE_LIMIT_FULL_CHECKS_PER_HOUR full checks
            were performed in the past hour.
    """
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    count_stmt = (
        select(func.count())
        .select_from(AtsCheck)
        .where(
            AtsCheck.user_id == user_uuid,
            AtsCheck.check_type == "full",
            AtsCheck.updated_at >= one_hour_ago,
        )
    )
    count_result = await session.exec(count_stmt)
    count: int = count_result.one()

    if count >= RATE_LIMIT_FULL_CHECKS_PER_HOUR:
        log.warning("ats_rate_limit_exceeded", user_id=str(user_uuid), count=count)
        raise AtsRateLimitError()


async def _check_ai_consent(session: AsyncSession, user_uuid: uuid.UUID) -> None:
    """Raise AtsConsentRequiredError if the user has not consented to AI analysis.

    Args:
        session: Async database session.
        user_uuid: UUID of the user.

    Raises:
        AtsConsentRequiredError: If the user profile lacks AI consent.
    """
    profile_stmt = select(UserProfile).where(UserProfile.user_id == user_uuid)
    profile_result = await session.exec(profile_stmt)
    profile = profile_result.first()

    if profile is None or not profile.ai_analysis_consented:
        log.warning("ats_consent_missing", user_id=str(user_uuid))
        raise AtsConsentRequiredError()


async def _get_resume(
    session: AsyncSession,
    user_uuid: uuid.UUID,
    resume_uuid: uuid.UUID,
) -> Resume:
    """Fetch a resume, validating ownership.

    Args:
        session: Async database session.
        user_uuid: UUID of the requesting user.
        resume_uuid: UUID of the resume.

    Returns:
        The Resume model instance.

    Raises:
        ResumeNotFoundError: If the resume does not exist or belongs to another user.
    """
    stmt = select(Resume).where(
        Resume.id == resume_uuid,
        Resume.user_id == user_uuid,
    )
    result = await session.exec(stmt)
    resume = result.first()

    if resume is None:
        log.warning(
            "ats_resume_not_found",
            user_id=str(user_uuid),
            resume_id=str(resume_uuid),
        )
        raise ResumeNotFoundError()

    return resume


async def _get_format_results(
    session: AsyncSession,
    resume: Resume,
) -> tuple[list[ats_rules.Finding], int]:
    """Return format findings and score, using a cached check when still fresh.

    A cached format-only check is considered fresh when its
    resume_updated_at matches the resume current updated_at.

    Args:
        session: Async database session.
        resume: The Resume model to analyse.

    Returns:
        A tuple of (findings, format_score).
    """
    cached_stmt = select(AtsCheck).where(
        AtsCheck.resume_id == resume.id,
        AtsCheck.job_id.is_(None),  # type: ignore[union-attr]
        AtsCheck.check_type == "format_only",
        AtsCheck.resume_updated_at == resume.updated_at,
        AtsCheck.prompt_version == PROMPT_VERSION,
    )
    cached_result = await session.exec(cached_stmt)
    cached = cached_result.first()

    if cached is not None:
        log.info(
            "ats_format_cache_hit",
            resume_id=str(resume.id),
            format_score=cached.format_score,
        )
        findings: list[ats_rules.Finding] = [
            ats_rules.Finding(**f) for f in cached.findings  # type: ignore[misc]
        ]
        return findings, cached.format_score

    fresh_check = await run_format_check(session, resume)
    findings = [
        ats_rules.Finding(**f) for f in fresh_check.findings  # type: ignore[misc]
    ]
    return findings, fresh_check.format_score



# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_format_check(session: AsyncSession, resume: Resume) -> AtsCheck:
    """Run all 16 deterministic format rules and upsert a format-only AtsCheck.

    Calculates a format compliance score from rule findings and applies
    severity caps: blocker findings cap the overall score at 15, critical
    findings cap at 30.

    Args:
        session: Async database session.
        resume: The Resume model to evaluate.

    Returns:
        The upserted AtsCheck (check_type="format_only").
    """
    findings = ats_rules.run_all_rules(resume)
    format_score, has_blocker, has_critical = ats_rules.calculate_format_score(findings)

    overall_score = format_score
    if has_blocker:
        overall_score = min(overall_score, 15)
    elif has_critical:
        overall_score = min(overall_score, 30)

    now = datetime.now(UTC)

    existing_stmt = select(AtsCheck).where(
        AtsCheck.resume_id == resume.id,
        AtsCheck.job_id.is_(None),  # type: ignore[union-attr]
        AtsCheck.check_type == "format_only",
    )
    existing_result = await session.exec(existing_stmt)
    check = existing_result.first()

    if check is not None:
        check.format_score = format_score
        check.overall_score = overall_score
        check.findings = [dict(f) for f in findings]  # type: ignore[misc]
        check.resume_updated_at = resume.updated_at
        check.prompt_version = PROMPT_VERSION
        check.updated_at = now
    else:
        check = AtsCheck(
            user_id=resume.user_id,
            resume_id=resume.id,
            job_id=None,
            check_type="format_only",
            prompt_version=PROMPT_VERSION,
            resume_updated_at=resume.updated_at,
            format_score=format_score,
            overall_score=overall_score,
            findings=[dict(f) for f in findings],  # type: ignore[misc]
            ai_analysis_available=False,
        )

    session.add(check)
    await session.flush()

    log.info(
        "ats_format_check_complete",
        resume_id=str(resume.id),
        format_score=format_score,
        overall_score=overall_score,
        finding_count=len(findings),
        has_blocker=has_blocker,
        has_critical=has_critical,
    )

    return check


async def run_full_check(
    session: AsyncSession,
    user_id: str,
    resume_id: str,
    job_id: str,
) -> AtsCheck:
    """Run a full ATS check combining format rules and Gemini AI analysis.

    Enforces rate limits and AI consent before running. Reuses a cached
    format-only check when the resume has not changed, then calls Gemini for
    keyword and content scoring. Falls back to format-only scores if Gemini
    is unavailable or fails.

    Args:
        session: Async database session.
        user_id: UUID string of the requesting user.
        resume_id: UUID string of the resume to check.
        job_id: UUID string of the job to check against.

    Returns:
        The upserted AtsCheck (check_type="full").

    Raises:
        AtsRateLimitError: If the user has exceeded the hourly rate limit.
        AtsConsentRequiredError: If the user has not consented to AI analysis.
        ResumeNotFoundError: If the resume does not exist or is not owned by user.
        JobNotFoundError: If the job does not exist.
    """
    user_uuid = uuid.UUID(user_id)
    resume_uuid = uuid.UUID(resume_id)
    job_uuid = uuid.UUID(job_id)

    await _check_rate_limit(session, user_uuid)
    await _check_ai_consent(session, user_uuid)

    resume = await _get_resume(session, user_uuid, resume_uuid)

    job_stmt = select(Job).where(Job.id == job_uuid)
    job_result = await session.exec(job_stmt)
    job = job_result.first()
    if job is None:
        log.warning("ats_job_not_found", job_id=job_id)
        raise JobNotFoundError()

    format_findings, format_score = await _get_format_results(session, resume)
    _, has_blocker, has_critical = ats_rules.calculate_format_score(format_findings)

    format_findings_summary = "; ".join(
        "[" + str(f["severity"]).upper() + "] " + str(f["title"])
        for f in format_findings
    ) or "No format issues detected."

    keyword_score: int | None = None
    content_score: int | None = None
    all_findings: list[dict[str, object]] = [dict(f) for f in format_findings]  # type: ignore[misc]
    all_suggestions: list[dict[str, object]] = []
    ai_analysis_available = False

    try:
        ai_result = await gemini_service.analyze_ats(
            resume_text=resume.raw_text,
            parsed_data=dict(resume.parsed_data),
            job_title=job.title,
            job_company=job.company,
            job_description=job.description,
            job_tags=list(job.tags) if job.tags else [],
            format_findings_summary=format_findings_summary,
        )

        keyword_score = ai_result.keyword_score
        content_score = ai_result.content_score

        for raw_finding in ai_result.keyword_findings:
            merged: dict[str, object] = dict(raw_finding)
            merged.setdefault("id", str(uuid.uuid4()))
            merged.setdefault("category", "keyword")
            merged.setdefault("confidence", "medium")
            merged.setdefault("dismissed", False)
            all_findings.append(merged)

        for raw_finding in ai_result.content_findings:
            merged = dict(raw_finding)
            merged.setdefault("id", str(uuid.uuid4()))
            merged.setdefault("category", "content")
            merged.setdefault("confidence", "medium")
            merged.setdefault("dismissed", False)
            all_findings.append(merged)

        all_suggestions = [dict(s) for s in ai_result.suggestions]

        overall_score = round(
            format_score * 0.3 + keyword_score * 0.4 + content_score * 0.3
        )

        if has_blocker:
            overall_score = min(overall_score, 15)
        elif has_critical:
            overall_score = min(overall_score, 30)

        ai_analysis_available = True

        log.info(
            "ats_full_check_ai_complete",
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            format_score=format_score,
            keyword_score=keyword_score,
            content_score=content_score,
            overall_score=overall_score,
        )

    except GeminiAnalysisError:
        log.warning(
            "ats_gemini_failed_fallback_format",
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
        )
        overall_score = format_score
        if has_blocker:
            overall_score = min(overall_score, 15)
        elif has_critical:
            overall_score = min(overall_score, 30)

    now = datetime.now(UTC)

    existing_stmt = select(AtsCheck).where(
        AtsCheck.resume_id == resume_uuid,
        AtsCheck.job_id == job_uuid,
    )
    existing_result = await session.exec(existing_stmt)
    check = existing_result.first()

    if check is not None:
        check.check_type = "full"
        check.prompt_version = PROMPT_VERSION
        check.resume_updated_at = resume.updated_at
        check.format_score = format_score
        check.keyword_score = keyword_score
        check.content_score = content_score
        check.overall_score = overall_score
        check.findings = all_findings
        check.suggestions = all_suggestions
        check.ai_analysis_available = ai_analysis_available
        check.updated_at = now
    else:
        check = AtsCheck(
            user_id=user_uuid,
            resume_id=resume_uuid,
            job_id=job_uuid,
            check_type="full",
            prompt_version=PROMPT_VERSION,
            resume_updated_at=resume.updated_at,
            format_score=format_score,
            keyword_score=keyword_score,
            content_score=content_score,
            overall_score=overall_score,
            findings=all_findings,
            suggestions=all_suggestions,
            ai_analysis_available=ai_analysis_available,
        )

    session.add(check)
    await session.flush()

    return check


async def get_check_results(
    session: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    resume_id: str | None = None,
) -> tuple[list[AtsCheck], int]:
    """Return a paginated list of ATS checks for a user.

    Args:
        session: Async database session.
        user_id: UUID string of the requesting user.
        page: 1-indexed page number.
        page_size: Number of items per page.
        resume_id: Optional UUID string to filter by a specific resume.

    Returns:
        A tuple of (list of AtsCheck, total count).
    """
    user_uuid = uuid.UUID(user_id)

    base_conditions = [AtsCheck.user_id == user_uuid]
    if resume_id is not None:
        base_conditions.append(AtsCheck.resume_id == uuid.UUID(resume_id))

    count_stmt = (
        select(func.count())
        .select_from(AtsCheck)
        .where(*base_conditions)
    )
    count_result = await session.exec(count_stmt)
    total: int = count_result.one()

    list_stmt = (
        select(AtsCheck)
        .where(*base_conditions)
        .order_by(col(AtsCheck.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    list_result = await session.exec(list_stmt)
    checks = list(list_result.all())

    log.info(
        "ats_check_results_fetched",
        user_id=user_id,
        total=total,
        page=page,
        page_size=page_size,
        returned=len(checks),
    )

    return checks, total


async def get_check_detail(
    session: AsyncSession,
    user_id: str,
    check_id: str,
) -> AtsCheck:
    """Return a single AtsCheck, validating ownership.

    Args:
        session: Async database session.
        user_id: UUID string of the requesting user.
        check_id: UUID string of the ATS check.

    Returns:
        The AtsCheck model instance.

    Raises:
        AtsCheckNotFoundError: If the check does not exist or belongs to another user.
    """
    user_uuid = uuid.UUID(user_id)
    check_uuid = uuid.UUID(check_id)

    stmt = select(AtsCheck).where(
        AtsCheck.id == check_uuid,
        AtsCheck.user_id == user_uuid,
    )
    result = await session.exec(stmt)
    check = result.first()

    if check is None:
        log.warning("ats_check_not_found", user_id=user_id, check_id=check_id)
        raise AtsCheckNotFoundError()

    return check


async def dismiss_finding(
    session: AsyncSession,
    user_id: str,
    check_id: str,
    finding_id: str,
    dismissed: bool,
) -> AtsCheck:
    """Toggle the dismissed state of a single finding within an ATS check.

    Args:
        session: Async database session.
        user_id: UUID string of the requesting user.
        check_id: UUID string of the ATS check.
        finding_id: The id field of the finding to update.
        dismissed: New dismissed state to apply.

    Returns:
        The updated AtsCheck model instance.

    Raises:
        AtsCheckNotFoundError: If the check does not exist or belongs to another user.
    """
    check = await get_check_detail(session, user_id, check_id)

    updated_findings: list[dict[str, object]] = []
    for finding in check.findings:
        if str(finding.get("id")) == finding_id:
            finding = dict(finding)
            finding["dismissed"] = dismissed
        updated_findings.append(finding)

    check.findings = updated_findings
    check.updated_at = datetime.now(UTC)
    session.add(check)
    await session.flush()

    log.info(
        "ats_finding_dismissed",
        check_id=check_id,
        finding_id=finding_id,
        dismissed=dismissed,
    )

    return check


def is_check_stale(check: AtsCheck, resume: Resume) -> bool:
    """Return True if the check should be re-run due to staleness.

    A check is considered stale if the resume has been updated since the
    check was run, or if the prompt version has changed.

    Args:
        check: An existing AtsCheck record.
        resume: The current Resume model.

    Returns:
        True if the check is stale and should be re-run.
    """
    return (
        check.resume_updated_at != resume.updated_at
        or check.prompt_version != PROMPT_VERSION
    )
