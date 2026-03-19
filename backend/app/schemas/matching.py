from __future__ import annotations

from pydantic import BaseModel

from app.schemas.job import JobResponse  # noqa: TCH001


class JobMatchResponse(BaseModel):
    """Single match result."""

    id: str
    job_id: str
    overall_score: int
    keyword_score: int
    ai_score: int | None
    skills_match: int | None
    experience_match: int | None
    education_match: int | None
    location_match: int | None
    salary_match: int | None
    strengths: list[str]
    gaps: list[str]
    recommendation: str | None
    created_at: str
    updated_at: str


class JobMatchWithJobResponse(BaseModel):
    """Match result with embedded job data."""

    match: JobMatchResponse
    job: JobResponse


class MatchResultsResponse(BaseModel):
    """Paginated match results."""

    matches: list[JobMatchWithJobResponse]
    total: int
    page: int
    page_size: int


class MatchAnalyzeResponse(BaseModel):
    """Response from running bulk analysis."""

    total_jobs_analyzed: int
    new_matches: int
    updated_matches: int
    top_score: int
    message: str


class SingleMatchAnalyzeResponse(BaseModel):
    """Response from single job deep analysis."""

    match: JobMatchResponse
    message: str
