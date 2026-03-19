from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class JobMatch(SQLModel, table=True):
    """Match result between a user profile/resume and a job listing."""

    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_job_match_user_job"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    job_id: uuid.UUID = Field(foreign_key="jobs.id", index=True)

    # Scores (0-100)
    overall_score: int = Field(default=0)
    keyword_score: int = Field(default=0)
    ai_score: int | None = Field(default=None)
    skills_match: int | None = Field(default=None)
    experience_match: int | None = Field(default=None)
    education_match: int | None = Field(default=None)
    location_match: int | None = Field(default=None)
    salary_match: int | None = Field(default=None)

    # AI analysis results
    strengths: list[str] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    gaps: list[str] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    recommendation: str | None = Field(default=None, max_length=50)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
