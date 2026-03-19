from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


class Resume(SQLModel, table=True):
    """A stored resume with file reference and parsed data."""

    __tablename__ = "resumes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    filename: str = Field(max_length=255)
    file_size: int
    file_type: str = Field(max_length=10)  # "pdf" or "docx"
    storage_key: str = Field(max_length=500, unique=True)
    raw_text: str = Field(default="", sa_column=Column(Text, default=""))
    parsed_data: dict = Field(default_factory=dict, sa_column=Column(JSON, default={}))
    is_primary: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
