from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile

from app.dependencies import get_current_user, get_db
from app.schemas.auth import UserResponse
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    OnboardingStepRequest,
    ResumeParseResponse,
)
from app.schemas.user import (
    EducationUpdateRequest,
    ExperienceUpdateRequest,
    LinkedInImportRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    SkillsUpdateRequest,
    UserWithProfileResponse,
)
from app.services.linkedin import import_linkedin_profile
from app.services.onboarding import (
    complete_onboarding,
    get_onboarding_status,
    save_onboarding_step,
)
from app.services.resume_parser import parse_resume
from app.services.user import (
    calculate_profile_completeness,
    deactivate_user,
    get_user_with_profile,
    update_education,
    update_experience,
    update_profile,
    update_skills,
)

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/users", tags=["users"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_response_from_model(user: object) -> UserResponse:
    """Build a UserResponse from a User SQLModel instance."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        auth_provider=user.auth_provider,
        is_active=user.is_active,
        created_at=str(user.created_at),
        updated_at=str(user.updated_at),
    )


def _profile_response_from_model(profile: object) -> ProfileResponse:
    """Build a ProfileResponse from a UserProfile SQLModel instance."""
    return ProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        phone=profile.phone,
        location=profile.location,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
        years_of_experience=profile.years_of_experience,
        desired_roles=profile.desired_roles,
        desired_locations=profile.desired_locations,
        min_salary=profile.min_salary,
        skills=profile.skills,
        education=profile.education,
        experience=profile.experience,
        certifications=profile.certifications,
        languages=profile.languages,
        summary=profile.summary,
        onboarding_completed=profile.onboarding_completed,
        profile_completeness=profile.profile_completeness,
    )


async def _recalculate_and_persist_completeness(
    session: AsyncSession,
    profile: object,
) -> None:
    """Recalculate profile completeness and persist the updated value."""
    score = await calculate_profile_completeness(profile)  # type: ignore[arg-type]
    profile.profile_completeness = score
    session.add(profile)  # type: ignore[arg-type]
    await session.flush()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserWithProfileResponse)
async def get_me(
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserWithProfileResponse:
    """Return the authenticated user together with their profile."""
    user_id = str(current_user["sub"])
    user, profile = await get_user_with_profile(session, user_id)

    return UserWithProfileResponse(
        user=_user_response_from_model(user),
        profile=_profile_response_from_model(profile),
    )


@router.put("/me", response_model=ProfileResponse)
async def update_me(
    body: ProfileUpdateRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update the authenticated user's profile fields."""
    user_id = str(current_user["sub"])
    data = body.model_dump(exclude_unset=True)

    profile = await update_profile(session, user_id, data)
    await _recalculate_and_persist_completeness(session, profile)

    return _profile_response_from_model(profile)


@router.put("/me/skills", response_model=ProfileResponse)
async def update_me_skills(
    body: SkillsUpdateRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Replace the authenticated user's skills list."""
    user_id = str(current_user["sub"])
    skills_dicts: list[dict[str, str]] = [
        skill.model_dump() for skill in body.skills  # type: ignore[misc]
    ]

    profile = await update_skills(session, user_id, skills_dicts)
    await _recalculate_and_persist_completeness(session, profile)

    return _profile_response_from_model(profile)


@router.put("/me/experience", response_model=ProfileResponse)
async def update_me_experience(
    body: ExperienceUpdateRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Replace the authenticated user's experience list."""
    user_id = str(current_user["sub"])
    experience_dicts: list[dict[str, str]] = [
        exp.model_dump() for exp in body.experience  # type: ignore[misc]
    ]

    profile = await update_experience(session, user_id, experience_dicts)
    await _recalculate_and_persist_completeness(session, profile)

    return _profile_response_from_model(profile)


@router.put("/me/education", response_model=ProfileResponse)
async def update_me_education(
    body: EducationUpdateRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Replace the authenticated user's education list."""
    user_id = str(current_user["sub"])
    education_dicts: list[dict[str, str]] = [
        edu.model_dump() for edu in body.education  # type: ignore[misc]
    ]

    profile = await update_education(session, user_id, education_dicts)
    await _recalculate_and_persist_completeness(session, profile)

    return _profile_response_from_model(profile)


@router.delete("/me", status_code=204)
async def delete_me(
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Soft-delete (deactivate) the authenticated user's account."""
    user_id = str(current_user["sub"])
    await deactivate_user(session, user_id)
    return Response(status_code=204)


@router.post("/me/linkedin/import")
async def import_linkedin(
    body: LinkedInImportRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str | list[str] | None]:
    """Import profile data from a LinkedIn public profile URL."""
    user_id = str(current_user["sub"])
    result = await import_linkedin_profile(session, user_id, body.linkedin_url)
    return result


# ---------------------------------------------------------------------------
# Onboarding endpoints
# ---------------------------------------------------------------------------

_MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB
_ALLOWED_RESUME_EXTENSIONS = (".pdf", ".docx")


@router.post("/me/resume/parse", response_model=ResumeParseResponse)
async def parse_resume_endpoint(
    file: UploadFile,
    current_user: dict[str, str | int] = Depends(get_current_user),
) -> ResumeParseResponse:
    """Upload and parse a resume file. Returns extracted fields for auto-fill."""
    filename = file.filename or "unknown"

    if not filename.lower().endswith(_ALLOWED_RESUME_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX files are accepted.",
        )

    content = await file.read()

    if len(content) > _MAX_RESUME_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5 MB.",
        )

    log.info(
        "resume_upload_received",
        user_id=str(current_user["sub"]),
        filename=filename,
        size=len(content),
    )

    try:
        parsed = await parse_resume(content, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        log.error(
            "resume_parse_failed",
            user_id=str(current_user["sub"]),
            filename=filename,
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to parse resume. Please try a different file.",
        ) from exc

    return ResumeParseResponse(
        full_name=parsed.get("full_name"),  # type: ignore[arg-type]
        email=parsed.get("email"),  # type: ignore[arg-type]
        phone=parsed.get("phone"),  # type: ignore[arg-type]
        location=parsed.get("location"),  # type: ignore[arg-type]
        summary=parsed.get("summary"),  # type: ignore[arg-type]
        skills=parsed.get("skills", []),  # type: ignore[arg-type]
        experience=parsed.get("experience", []),  # type: ignore[arg-type]
        education=parsed.get("education", []),  # type: ignore[arg-type]
        certifications=parsed.get("certifications", []),  # type: ignore[arg-type]
    )


@router.put("/me/onboarding", response_model=OnboardingStatusResponse)
async def save_onboarding_step_endpoint(
    step_data: OnboardingStepRequest,
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OnboardingStatusResponse:
    """Save onboarding wizard step data."""
    user_id = str(current_user["sub"])
    data = step_data.model_dump(exclude_unset=True)

    await save_onboarding_step(session, user_id, data)

    status = await get_onboarding_status(session, user_id)
    return OnboardingStatusResponse(
        completed=status["completed"],  # type: ignore[arg-type]
        profile_completeness=status["profile_completeness"],  # type: ignore[arg-type]
        missing_fields=status["missing_fields"],  # type: ignore[arg-type]
    )


@router.post("/me/onboarding/complete", response_model=OnboardingStatusResponse)
async def complete_onboarding_endpoint(
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OnboardingStatusResponse:
    """Mark onboarding as complete."""
    user_id = str(current_user["sub"])

    await complete_onboarding(session, user_id)

    status = await get_onboarding_status(session, user_id)
    return OnboardingStatusResponse(
        completed=status["completed"],  # type: ignore[arg-type]
        profile_completeness=status["profile_completeness"],  # type: ignore[arg-type]
        missing_fields=status["missing_fields"],  # type: ignore[arg-type]
    )


@router.get("/me/onboarding/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status_endpoint(
    current_user: dict[str, str | int] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OnboardingStatusResponse:
    """Get onboarding progress."""
    user_id = str(current_user["sub"])

    status = await get_onboarding_status(session, user_id)
    return OnboardingStatusResponse(
        completed=status["completed"],  # type: ignore[arg-type]
        profile_completeness=status["profile_completeness"],  # type: ignore[arg-type]
        missing_fields=status["missing_fields"],  # type: ignore[arg-type]
    )
