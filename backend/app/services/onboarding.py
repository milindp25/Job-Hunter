from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from sqlmodel import select

from app.exceptions import UserNotFoundError
from app.models.user import UserProfile
from app.services.user import calculate_profile_completeness

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

# Fields that contribute to profile completeness and the labels used when
# reporting missing items.  The keys must match UserProfile attribute names.
_COMPLETENESS_FIELDS: dict[str, str] = {
    "phone": "phone",
    "location": "location",
    "summary": "summary",
    "linkedin_url": "linkedin_url",
    "skills": "skills",
    "experience": "experience",
    "education": "education",
    "desired_roles": "desired_roles",
    "desired_locations": "desired_locations",
    "min_salary": "min_salary",
    "certifications": "certifications",
}

# Profile fields that can be updated through onboarding steps.
_ALLOWED_FIELDS: set[str] = {
    "phone",
    "location",
    "linkedin_url",
    "github_url",
    "portfolio_url",
    "summary",
    "full_name",
    "years_of_experience",
    "desired_roles",
    "desired_locations",
    "min_salary",
    "skills",
    "education",
    "experience",
    "certifications",
    "languages",
}


async def _get_profile(session: AsyncSession, user_id: str) -> UserProfile:
    """Fetch a user profile by user_id, raising UserNotFoundError if missing."""
    statement = select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
    result = await session.exec(statement)
    profile = result.first()
    if profile is None:
        log.warning("onboarding_profile_not_found", user_id=user_id)
        raise UserNotFoundError(detail="User profile not found")
    return profile


def _compute_missing_fields(profile: UserProfile) -> list[str]:
    """Return a list of field names that are empty/unset and would improve the score."""
    missing: list[str] = []
    for field, label in _COMPLETENESS_FIELDS.items():
        value = getattr(profile, field, None)
        is_empty = (
            value is None
            or (isinstance(value, list) and len(value) == 0)
            or (isinstance(value, str) and not value.strip())
        )
        if is_empty:
            missing.append(label)
    return missing


async def save_onboarding_step(
    session: AsyncSession,
    user_id: str,
    step_data: dict[str, str | int | list[str] | list[dict[str, str]] | None],
) -> UserProfile:
    """Save data from an onboarding wizard step.

    Merges *step_data* into the existing profile (partial update).
    Recalculates ``profile_completeness`` after each save.
    """
    profile = await _get_profile(session, user_id)

    updated_fields: list[str] = []
    for field, value in step_data.items():
        if field not in _ALLOWED_FIELDS:
            log.debug("onboarding_field_skipped", field=field, user_id=user_id)
            continue
        if hasattr(profile, field):
            setattr(profile, field, value)
            updated_fields.append(field)

    # Recalculate completeness
    profile.profile_completeness = await calculate_profile_completeness(profile)

    session.add(profile)
    await session.flush()

    log.info(
        "onboarding_step_saved",
        user_id=user_id,
        updated_fields=updated_fields,
        profile_completeness=profile.profile_completeness,
    )
    return profile


async def complete_onboarding(
    session: AsyncSession,
    user_id: str,
) -> UserProfile:
    """Mark onboarding as complete.

    Sets ``onboarding_completed=True`` and performs a final
    ``profile_completeness`` recalculation.
    """
    profile = await _get_profile(session, user_id)

    profile.onboarding_completed = True
    profile.profile_completeness = await calculate_profile_completeness(profile)

    session.add(profile)
    await session.flush()

    log.info(
        "onboarding_completed",
        user_id=user_id,
        profile_completeness=profile.profile_completeness,
    )
    return profile


async def get_onboarding_status(
    session: AsyncSession,
    user_id: str,
) -> dict[str, bool | int | list[str]]:
    """Return onboarding progress.

    Returns:
        dict with:
        - completed: bool
        - profile_completeness: int
        - missing_fields: list[str] (fields that would increase the score)
    """
    profile = await _get_profile(session, user_id)

    missing = _compute_missing_fields(profile)

    log.debug(
        "onboarding_status_retrieved",
        user_id=user_id,
        completed=profile.onboarding_completed,
        profile_completeness=profile.profile_completeness,
        missing_count=len(missing),
    )

    return {
        "completed": profile.onboarding_completed,
        "profile_completeness": profile.profile_completeness,
        "missing_fields": missing,
    }
