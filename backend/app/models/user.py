from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Core user account model for authentication and identity."""

    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=320)
    hashed_password: str | None = Field(default=None, max_length=128)
    full_name: str = Field(max_length=255)
    avatar_url: str | None = Field(default=None, max_length=500)
    auth_provider: str = Field(default="email", max_length=20)
    auth_provider_id: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserProfile(SQLModel, table=True):
    """Extended user profile with job-seeking preferences and background."""

    __tablename__ = "user_profiles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    phone: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    portfolio_url: str | None = Field(default=None, max_length=500)
    years_of_experience: int | None = Field(default=None)
    desired_roles: list[str] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    desired_locations: list[str] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    min_salary: int | None = Field(default=None)
    skills: list[dict] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    education: list[dict] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    experience: list[dict] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    certifications: list[str] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    languages: list[dict] = Field(default_factory=list, sa_column=Column(JSON, default=[]))
    summary: str | None = Field(default=None)
    onboarding_completed: bool = Field(default=False)
    profile_completeness: int = Field(default=0)
    ai_analysis_consented: bool = Field(default=False)
