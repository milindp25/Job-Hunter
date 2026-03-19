from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Query
from sqlmodel import select

from app.dependencies import get_current_user, get_db
from app.models.resume import Resume
from app.schemas.ats import (
    AtsCheckListResponse,
    AtsCheckRequest,
    AtsCheckResponse,
    AtsDismissRequest,
    AtsFindingResponse,
    AtsSuggestionResponse,
)
from app.services import ats_checker

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/ats", tags=["ats"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_response(check: object, is_stale: bool = False) -> AtsCheckResponse:
    """Build an AtsCheckResponse from an AtsCheck SQLModel instance."""
    findings = [
        AtsFindingResponse(
            id=str(f.get("id", "")),  # type: ignore[union-attr]
            category=str(f.get("category", "")),  # type: ignore[union-attr]
            severity=str(f.get("severity", "")),  # type: ignore[union-attr]
            confidence=str(f.get("confidence", "medium")),  # type: ignore[union-attr]
            rule_id=str(f.get("rule_id", "")),  # type: ignore[union-attr]
            title=str(f.get("title", "")),  # type: ignore[union-attr]
            detail=str(f.get("detail", "")),  # type: ignore[union-attr]
            suggestion=str(f.get("suggestion", "")),  # type: ignore[union-attr]
            section=f.get("section"),  # type: ignore[union-attr]
            metadata=f.get("metadata", {}),  # type: ignore[union-attr]
            dismissed=bool(f.get("dismissed", False)),  # type: ignore[union-attr]
        )
        for f in check.findings  # type: ignore[attr-defined]
    ]

    suggestions = [
        AtsSuggestionResponse(
            section=str(s.get("section", "")),  # type: ignore[union-attr]
            before=str(s.get("before", "")),  # type: ignore[union-attr]
            after=str(s.get("after", "")),  # type: ignore[union-attr]
            reason=str(s.get("reason", "")),  # type: ignore[union-attr]
            estimated_impact=str(s.get("estimated_impact", "")),  # type: ignore[union-attr]
        )
        for s in check.suggestions  # type: ignore[attr-defined]
    ]

    return AtsCheckResponse(
        id=str(check.id),  # type: ignore[attr-defined]
        resume_id=str(check.resume_id),  # type: ignore[attr-defined]
        job_id=str(check.job_id) if check.job_id is not None else None,  # type: ignore[attr-defined]
        check_type=check.check_type,  # type: ignore[attr-defined]
        overall_score=check.overall_score,  # type: ignore[attr-defined]
        format_score=check.format_score,  # type: ignore[attr-defined]
        keyword_score=check.keyword_score,  # type: ignore[attr-defined]
        content_score=check.content_score,  # type: ignore[attr-defined]
        findings=findings,
        suggestions=suggestions,
        ai_analysis_available=check.ai_analysis_available,  # type: ignore[attr-defined]
        is_stale=is_stale,
        created_at=str(check.created_at),  # type: ignore[attr-defined]
        updated_at=str(check.updated_at),  # type: ignore[attr-defined]
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/check", response_model=AtsCheckResponse)
async def run_check(
    request: AtsCheckRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AtsCheckResponse:
    """Run an ATS compliance check against a resume, optionally against a job.

    When job_id is provided, performs a full check combining deterministic
    format rules with Gemini AI keyword and content analysis. Without job_id,
    runs format-only checks using the 16 deterministic rules.
    """
    user_id = str(current_user["sub"])
    log.info(
        "ats_check_requested",
        user_id=user_id,
        resume_id=request.resume_id,
        job_id=request.job_id,
    )

    if request.job_id is not None:
        check = await ats_checker.run_full_check(
            session, user_id, request.resume_id, request.job_id
        )
        return _check_response(check)

    resume_stmt = select(Resume).where(
        Resume.id == uuid.UUID(request.resume_id),
        Resume.user_id == uuid.UUID(user_id),
    )
    resume_result = await session.exec(resume_stmt)
    resume = resume_result.first()

    if resume is None:
        from app.exceptions import ResumeNotFoundError  # noqa: PLC0415

        raise ResumeNotFoundError()

    check = await ats_checker.run_format_check(session, resume)
    return _check_response(check)


@router.get("/results", response_model=AtsCheckListResponse)
async def get_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resume_id: str | None = Query(None),
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AtsCheckListResponse:
    """Get paginated ATS check results for the authenticated user.

    Returns checks sorted by creation date in descending order.
    Optionally filters by resume_id.
    """
    user_id = str(current_user["sub"])

    checks, total = await ats_checker.get_check_results(
        session, user_id, page, page_size, resume_id
    )

    return AtsCheckListResponse(
        checks=[_check_response(check) for check in checks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/results/{check_id}", response_model=AtsCheckResponse)
async def get_check_detail(
    check_id: str,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AtsCheckResponse:
    """Get detailed ATS check result for a specific check.

    Returns the full check including all findings and AI-generated suggestions.
    """
    user_id = str(current_user["sub"])

    check = await ats_checker.get_check_detail(session, user_id, check_id)
    return _check_response(check)


@router.patch(
    "/results/{check_id}/findings/{finding_id}/dismiss",
    response_model=AtsCheckResponse,
)
async def dismiss_finding(
    check_id: str,
    finding_id: str,
    request: AtsDismissRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AtsCheckResponse:
    """Dismiss or un-dismiss a specific finding within an ATS check.

    Toggling dismissed allows users to acknowledge known issues without
    them cluttering the findings list.
    """
    user_id = str(current_user["sub"])
    log.info(
        "ats_finding_dismiss_requested",
        user_id=user_id,
        check_id=check_id,
        finding_id=finding_id,
        dismissed=request.dismissed,
    )

    check = await ats_checker.dismiss_finding(
        session, user_id, check_id, finding_id, request.dismissed
    )
    return _check_response(check)
