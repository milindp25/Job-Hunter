from __future__ import annotations

import httpx
import structlog

from app.services.job_clients.base import NormalizedJob

log = structlog.get_logger()


class AdzunaClient:
    """Client for the Adzuna job search API.

    Adzuna requires an app_id and app_key for authentication, passed as
    query parameters. The API supports server-side pagination and filtering.
    """

    source_name: str = "adzuna"

    _BASE_URL: str = "https://api.adzuna.com/v1/api/jobs/us/search"

    def __init__(self, app_id: str, app_key: str) -> None:
        self._app_id = app_id
        self._app_key = app_key

    def is_configured(self) -> bool:
        """Check if Adzuna API credentials are provided."""
        return bool(self._app_id and self._app_key)

    async def fetch_jobs(
        self,
        query: str = "",
        location: str | None = None,
        page: int = 1,
    ) -> list[NormalizedJob]:
        """Fetch jobs from the Adzuna API.

        Adzuna uses 1-indexed pages and embeds the page number in the URL path.
        """
        if not self.is_configured():
            log.info("adzuna_not_configured")
            return []

        try:
            url = f"{self._BASE_URL}/{page}"
            params: dict[str, str] = {
                "app_id": self._app_id,
                "app_key": self._app_key,
                "results_per_page": "20",
                "content-type": "application/json",
            }

            if query:
                params["what"] = query

            if location:
                params["where"] = location

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            results: list[dict[str, object]] = data.get("results", [])
            normalized = [self._normalize(job) for job in results]
            log.info(
                "adzuna_fetch_complete",
                count=len(normalized),
                query=query,
                page=page,
                total=data.get("count", 0),
            )
            return normalized

        except httpx.HTTPError as exc:
            log.warning("adzuna_fetch_failed", error=str(exc))
            return []

    def _normalize(self, raw: dict[str, object]) -> NormalizedJob:
        """Normalize an Adzuna job to common format."""
        # Extract nested company name
        company_data = raw.get("company", {})
        company_name = "Unknown Company"
        if isinstance(company_data, dict):
            company_name = str(company_data.get("display_name", "Unknown Company"))

        # Extract nested location
        location_data = raw.get("location", {})
        location_str: str | None = None
        if isinstance(location_data, dict):
            display = str(location_data.get("display_name", ""))
            location_str = display or None

        # Check if remote based on location or title
        title = str(raw.get("title", "Unknown Position"))
        is_remote = "remote" in title.lower() or (
            location_str is not None and "remote" in location_str.lower()
        )

        # Extract category as tag
        category_data = raw.get("category", {})
        tags: list[str] = []
        if isinstance(category_data, dict) and category_data.get("label"):
            tags.append(str(category_data["label"]))

        # Parse salary values
        salary_min = self._parse_salary(raw.get("salary_min"))
        salary_max = self._parse_salary(raw.get("salary_max"))
        salary_currency = "GBP" if (salary_min or salary_max) else None

        # Determine job type from contract fields
        contract_type = str(raw.get("contract_type", "")).lower()
        if "part" in contract_type:
            job_type = "part-time"
        elif "contract" in contract_type:
            job_type = "contract"
        else:
            job_type = "full-time"

        return NormalizedJob(
            external_id=str(raw.get("id", "")),
            source="adzuna",
            title=title,
            company=company_name,
            location=location_str,
            is_remote=is_remote,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            description=str(raw.get("description", "")),
            job_type=job_type,
            url=str(raw.get("redirect_url", "")),
            tags=tags,
            raw_data=raw,
            posted_at=str(raw.get("created")) if raw.get("created") else None,
        )

    def _parse_salary(self, value: object) -> int | None:
        """Parse salary value to integer."""
        if value is None:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
