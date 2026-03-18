from __future__ import annotations

from pydantic import BaseModel


class OnboardingStepRequest(BaseModel):
    """Generic onboarding step data -- matches any combination of profile fields."""

    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None
    full_name: str | None = None
    years_of_experience: int | None = None
    desired_roles: list[str] | None = None
    desired_locations: list[str] | None = None
    min_salary: int | None = None
    skills: list[dict[str, str | float]] | None = None
    education: list[dict[str, str | None]] | None = None
    experience: list[dict[str, str | None]] | None = None
    certifications: list[str] | None = None
    languages: list[dict[str, str]] | None = None


class OnboardingStatusResponse(BaseModel):
    """Response describing onboarding progress."""

    completed: bool
    profile_completeness: int
    missing_fields: list[str]


class ResumeParseResponse(BaseModel):
    """Structured data extracted from a parsed resume."""

    full_name: str | None
    email: str | None
    phone: str | None
    location: str | None
    summary: str | None
    skills: list[str]
    experience: list[dict[str, str | None]]
    education: list[dict[str, str | None]]
    certifications: list[str]
