from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from sqlmodel import select

from app.exceptions import UserNotFoundError
from app.models.user import User, UserProfile

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()


async def get_user_with_profile(
    session: AsyncSession,
    user_id: str,
) -> tuple[User, UserProfile]:
    """Get user and their profile. Raises UserNotFoundError if not found."""
    user_statement = select(User).where(User.id == uuid.UUID(user_id))
    user_result = await session.exec(user_statement)
    user = user_result.first()
    if user is None:
        log.warning("user_not_found", user_id=user_id)
        raise UserNotFoundError()

    profile_statement = select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
    profile_result = await session.exec(profile_statement)
    profile = profile_result.first()
    if profile is None:
        log.warning("user_profile_not_found", user_id=user_id)
        raise UserNotFoundError(detail="User profile not found")

    return user, profile


async def update_profile(
    session: AsyncSession,
    user_id: str,
    data: dict[str, str | int | list[str] | list[dict[str, str]] | bool | None],
) -> UserProfile:
    """Update user profile fields. Only updates provided fields (partial update)."""
    profile_statement = select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
    profile_result = await session.exec(profile_statement)
    profile = profile_result.first()
    if profile is None:
        log.warning("profile_not_found_for_update", user_id=user_id)
        raise UserNotFoundError(detail="User profile not found")

    for field, value in data.items():
        if hasattr(profile, field):
            setattr(profile, field, value)

    session.add(profile)
    await session.flush()

    log.info("profile_updated", user_id=user_id, fields=list(data.keys()))
    return profile


async def update_skills(
    session: AsyncSession,
    user_id: str,
    skills: list[dict[str, str]],
) -> UserProfile:
    """Replace the skills list on user profile."""
    profile_statement = select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
    profile_result = await session.exec(profile_statement)
    profile = profile_result.first()
    if profile is None:
        log.warning("profile_not_found_for_skills_update", user_id=user_id)
        raise UserNotFoundError(detail="User profile not found")

    profile.skills = skills
    session.add(profile)
    await session.flush()

    log.info("skills_updated", user_id=user_id, count=len(skills))
    return profile


async def update_experience(
    session: AsyncSession,
    user_id: str,
    experience: list[dict[str, str]],
) -> UserProfile:
    """Replace the experience list on user profile."""
    profile_statement = select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
    profile_result = await session.exec(profile_statement)
    profile = profile_result.first()
    if profile is None:
        log.warning("profile_not_found_for_experience_update", user_id=user_id)
        raise UserNotFoundError(detail="User profile not found")

    profile.experience = experience
    session.add(profile)
    await session.flush()

    log.info("experience_updated", user_id=user_id, count=len(experience))
    return profile


async def update_education(
    session: AsyncSession,
    user_id: str,
    education: list[dict[str, str]],
) -> UserProfile:
    """Replace the education list on user profile."""
    profile_statement = select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
    profile_result = await session.exec(profile_statement)
    profile = profile_result.first()
    if profile is None:
        log.warning("profile_not_found_for_education_update", user_id=user_id)
        raise UserNotFoundError(detail="User profile not found")

    profile.education = education
    session.add(profile)
    await session.flush()

    log.info("education_updated", user_id=user_id, count=len(education))
    return profile


async def calculate_profile_completeness(profile: UserProfile) -> int:
    """Calculate profile completeness percentage (0-100).

    Scoring:
    - Has phone: +5
    - Has location: +5
    - Has summary: +10
    - Has linkedin_url: +5
    - Has at least 1 skill: +15
    - Has at least 3 skills: +10 (additional)
    - Has at least 1 experience: +15
    - Has at least 1 education: +10
    - Has desired_roles: +10
    - Has desired_locations: +5
    - Has min_salary: +5
    - Has certifications: +5
    Total possible: 100
    """
    score = 0

    if profile.phone:
        score += 5
    if profile.location:
        score += 5
    if profile.summary:
        score += 10
    if profile.linkedin_url:
        score += 5

    if profile.skills and len(profile.skills) >= 1:
        score += 15
    if profile.skills and len(profile.skills) >= 3:
        score += 10

    if profile.experience and len(profile.experience) >= 1:
        score += 15
    if profile.education and len(profile.education) >= 1:
        score += 10

    if profile.desired_roles and len(profile.desired_roles) >= 1:
        score += 10
    if profile.desired_locations and len(profile.desired_locations) >= 1:
        score += 5
    if profile.min_salary is not None:
        score += 5
    if profile.certifications and len(profile.certifications) >= 1:
        score += 5

    return score


async def deactivate_user(
    session: AsyncSession,
    user_id: str,
) -> None:
    """Soft-delete user by setting is_active=False."""
    user_statement = select(User).where(User.id == uuid.UUID(user_id))
    user_result = await session.exec(user_statement)
    user = user_result.first()
    if user is None:
        log.warning("deactivate_user_not_found", user_id=user_id)
        raise UserNotFoundError()

    user.is_active = False
    session.add(user)
    await session.flush()

    log.info("user_deactivated", user_id=user_id)
