from __future__ import annotations

from typing import Protocol, TypedDict


class NormalizedJob(TypedDict):
    """Common job format that all API clients normalize to."""

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
    raw_data: dict[str, object]
    posted_at: str | None  # ISO format datetime string


class JobAPIClient(Protocol):
    """Protocol that all job API clients must implement."""

    source_name: str

    async def fetch_jobs(
        self,
        query: str = "",
        location: str | None = None,
        page: int = 1,
    ) -> list[NormalizedJob]:
        """Fetch and normalize jobs from the external API."""
        ...

    def is_configured(self) -> bool:
        """Check if this client has the required API keys configured."""
        ...
