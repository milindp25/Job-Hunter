from __future__ import annotations

from pydantic import BaseModel

from app.schemas.auth import UserResponse  # noqa: TCH001


class ProfileResponse(BaseModel):
    """Full user profile representation."""

    id: str
    user_id: str
    phone: str | None
    location: str | None
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    years_of_experience: int | None
    desired_roles: list[str]
    desired_locations: list[str]
    min_salary: int | None
    skills: list[dict[str, str | float]]
    education: list[dict[str, str | None]]
    experience: list[dict[str, str | None]]
    certifications: list[str]
    languages: list[dict[str, str]]
    summary: str | None
    onboarding_completed: bool
    profile_completeness: int


class ProfileUpdateRequest(BaseModel):
    """Request body for updating general profile fields."""

    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    years_of_experience: int | None = None
    desired_roles: list[str] | None = None
    desired_locations: list[str] | None = None
    min_salary: int | None = None
    summary: str | None = None


class SkillItem(BaseModel):
    """A single skill entry."""

    name: str
    level: str  # beginner | intermediate | advanced | expert
    years: float


class SkillsUpdateRequest(BaseModel):
    """Request body for replacing the skills list."""

    skills: list[SkillItem]


class ExperienceItem(BaseModel):
    """A single work experience entry."""

    company: str
    title: str
    description: str
    start_date: str
    end_date: str | None = None


class ExperienceUpdateRequest(BaseModel):
    """Request body for replacing the experience list."""

    experience: list[ExperienceItem]


class EducationItem(BaseModel):
    """A single education entry."""

    institution: str
    degree: str
    field: str
    start_date: str
    end_date: str | None = None


class EducationUpdateRequest(BaseModel):
    """Request body for replacing the education list."""

    education: list[EducationItem]


class UserWithProfileResponse(BaseModel):
    """Combined user and profile response."""

    user: UserResponse
    profile: ProfileResponse
