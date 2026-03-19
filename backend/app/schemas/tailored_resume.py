from __future__ import annotations

from pydantic import BaseModel, Field


class TailorResumeRequest(BaseModel):
    """Request body for tailoring a resume to a job."""

    resume_id: str = Field(description="UUID of the resume to tailor")
    job_id: str = Field(description="UUID of the target job")


class TailoredResumeResponse(BaseModel):
    """Response representing a tailored resume."""

    id: str
    resume_id: str
    job_id: str
    tailored_summary: str | None
    tailored_experience: list[dict[str, object]]
    tailored_skills: list[str]
    keyword_matches: list[str]
    keyword_gaps: list[str]
    match_score_before: int | None
    match_score_after: int | None
    ai_model: str
    created_at: str


class TailoredResumeListResponse(BaseModel):
    """Response containing a list of tailored resumes."""

    items: list[TailoredResumeResponse]
    total: int
