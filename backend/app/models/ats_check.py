from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class AtsCheck(SQLModel, table=True):
    """ATS compliance check result for a resume, optionally against a job."""

    __tablename__ = "ats_checks"
    __table_args__ = (
        UniqueConstraint("resume_id", "job_id", name="uq_ats_check_resume_job"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    resume_id: uuid.UUID = Field(foreign_key="resumes.id", index=True)
    job_id: uuid.UUID | None = Field(default=None, foreign_key="jobs.id", index=True)

    check_type: str = Field(max_length=20)  # "format_only" | "full"
    prompt_version: str = Field(default="v1", max_length=10)
    resume_updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    overall_score: int = Field(default=0)
    format_score: int = Field(default=0)
    keyword_score: int | None = Field(default=None)
    content_score: int | None = Field(default=None)

    findings: list[dict[str, object]] = Field(
        default_factory=list,
        sa_column=Column(JSON, default=[]),
    )
    suggestions: list[dict[str, object]] = Field(
        default_factory=list,
        sa_column=Column(JSON, default=[]),
    )

    ai_analysis_available: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
