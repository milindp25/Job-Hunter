from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class Job(SQLModel, table=True):
    """A job listing fetched from an external job board API."""

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_job_source_external_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    external_id: str = Field(index=True, max_length=255)
    source: str = Field(max_length=50)  # "remoteok" | "themuse" | "adzuna" | "usajobs"
    title: str = Field(max_length=500)
    company: str = Field(max_length=255)
    location: str | None = Field(default=None, max_length=500)
    is_remote: bool = Field(default=False)
    salary_min: int | None = Field(default=None)
    salary_max: int | None = Field(default=None)
    salary_currency: str | None = Field(default="USD", max_length=10)
    description: str = Field(default="", sa_column=Column(Text, default=""))
    job_type: str = Field(default="full-time", max_length=20)
    url: str = Field(max_length=1000)
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    raw_data: dict = Field(default_factory=dict, sa_column=Column(JSON, default={}))
    posted_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(default=True)


class SavedJob(SQLModel, table=True):
    """A job saved/bookmarked by a user."""

    __tablename__ = "saved_jobs"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_saved_job_user_job"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    job_id: uuid.UUID = Field(foreign_key="jobs.id", index=True)
    saved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = Field(default=None, max_length=1000)
