from __future__ import annotations

from pydantic import BaseModel


class JobResponse(BaseModel):
    """Single job listing representation."""

    id: str
    external_id: str
    source: str
    title: str
    company: str
    location: str | None
    is_remote: bool
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    description: str
    job_type: str
    url: str
    tags: list[str]
    posted_at: str | None
    is_active: bool
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int


class JobSearchParams(BaseModel):
    """Query parameters for job search."""

    query: str = ""
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: str | None = None
    source: str | None = None
    is_remote: bool | None = None
    page: int = 1
    page_size: int = 20


class SavedJobResponse(BaseModel):
    """A saved/bookmarked job."""

    id: str
    job: JobResponse
    saved_at: str
    notes: str | None


class SavedJobListResponse(BaseModel):
    """List of saved jobs."""

    saved_jobs: list[SavedJobResponse]
    total: int


class SaveJobRequest(BaseModel):
    """Request to save a job with optional notes."""

    notes: str | None = None


class JobFetchResponse(BaseModel):
    """Response from a job fetch operation."""

    sources_fetched: list[str]
    total_new_jobs: int
    total_updated_jobs: int
    message: str
