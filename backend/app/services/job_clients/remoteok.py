from __future__ import annotations

import httpx
import structlog

from app.services.job_clients.base import NormalizedJob

log = structlog.get_logger()


class RemoteOKClient:
    """Client for the RemoteOK job board API.

    RemoteOK is a free API with no authentication required.
    All jobs listed are remote positions.
    """

    source_name: str = "remoteok"

    _PAGE_SIZE: int = 20

    def is_configured(self) -> bool:
        """RemoteOK requires no API key."""
        return True

    async def fetch_jobs(
        self,
        query: str = "",
        location: str | None = None,
        page: int = 1,
    ) -> list[NormalizedJob]:
        """Fetch remote jobs from RemoteOK API.

        RemoteOK does not support server-side pagination or query filtering,
        so both are handled client-side after fetching the full listing.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = "https://remoteok.com/api"
                headers = {"User-Agent": "JobHunter/1.0"}
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            # First element is a metadata/legal dict, actual jobs start at index 1
            jobs: list[dict[str, object]] = data[1:] if len(data) > 1 else []

            # Client-side query filtering
            if query:
                query_lower = query.lower()
                jobs = [
                    j
                    for j in jobs
                    if query_lower in str(j.get("position", "")).lower()
                    or query_lower in str(j.get("company", "")).lower()
                    or query_lower in " ".join(
                        tag if isinstance(tag, str) else str(tag)
                        for tag in (j.get("tags") if isinstance(j.get("tags"), list) else [])
                    ).lower()
                ]

            # Client-side pagination
            start = (page - 1) * self._PAGE_SIZE
            jobs = jobs[start : start + self._PAGE_SIZE]

            normalized = [self._normalize(job) for job in jobs]
            log.info("remoteok_fetch_complete", count=len(normalized), query=query, page=page)
            return normalized

        except httpx.HTTPError as exc:
            log.warning("remoteok_fetch_failed", error=str(exc))
            return []

    def _normalize(self, raw: dict[str, object]) -> NormalizedJob:
        """Normalize a RemoteOK job to common format."""
        raw_id = str(raw.get("id", ""))
        raw_tags = raw.get("tags")
        tags: list[str] = (
            [str(t) for t in raw_tags] if isinstance(raw_tags, list) else []
        )

        return NormalizedJob(
            external_id=raw_id,
            source="remoteok",
            title=str(raw.get("position", "Unknown Position")),
            company=str(raw.get("company", "Unknown Company")),
            location=str(raw.get("location", "")) or None,
            is_remote=True,  # All RemoteOK jobs are remote
            salary_min=self._parse_salary(raw.get("salary_min")),
            salary_max=self._parse_salary(raw.get("salary_max")),
            salary_currency="USD",
            description=str(raw.get("description", "")),
            job_type="full-time",
            url=str(raw.get("url", f"https://remoteok.com/l/{raw_id}")),
            tags=tags,
            raw_data=raw,
            posted_at=str(raw.get("date")) if raw.get("date") else None,
        )

    def _parse_salary(self, value: object) -> int | None:
        """Parse salary value from various formats to an integer."""
        if value is None:
            return None
        try:
            cleaned = str(value).replace(",", "").replace("$", "").strip()
            return int(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
