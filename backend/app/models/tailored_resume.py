from __future__ import annotations

import uuid  # noqa: TCH003
from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class TailoredResume(SQLModel, table=True):
    """AI-tailored version of a resume for a specific job listing."""

    __tablename__ = "tailored_resumes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    resume_id: uuid.UUID = Field(foreign_key="resumes.id", index=True)
    job_id: uuid.UUID = Field(foreign_key="jobs.id", index=True)

    # Tailored content
    tailored_summary: str | None = Field(default=None)
    tailored_experience: list[dict[str, object]] = Field(
        default_factory=list, sa_column=Column(JSON, default=[])
    )
    tailored_skills: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, default=[])
    )

    # Analysis
    keyword_matches: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, default=[])
    )
    keyword_gaps: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, default=[])
    )
    match_score_before: int | None = Field(default=None)
    match_score_after: int | None = Field(default=None)
    ai_model: str = Field(default="gemini-2.0-flash")
    prompt_version: str = Field(default="v1")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
