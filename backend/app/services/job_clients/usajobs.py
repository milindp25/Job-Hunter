from __future__ import annotations

import httpx
import structlog

from app.services.job_clients.base import NormalizedJob

log = structlog.get_logger()


class USAJobsClient:
    """Client for the USAJobs federal employment API.

    USAJobs requires an API key (Authorization-Key header) and an email
    address (User-Agent header) for authentication.
    """

    source_name: str = "usajobs"

    _BASE_URL: str = "https://data.usajobs.gov/api/Search"
    _PAGE_SIZE: int = 25  # USAJobs default page size

    def __init__(self, api_key: str, email: str) -> None:
        self._api_key = api_key
        self._email = email

    def is_configured(self) -> bool:
        """Check if USAJobs API credentials are provided."""
        return bool(self._api_key and self._email)

    async def fetch_jobs(
        self,
        query: str = "",
        location: str | None = None,
        page: int = 1,
    ) -> list[NormalizedJob]:
        """Fetch federal jobs from the USAJobs API.

        USAJobs uses 1-indexed pages and requires auth headers.
        """
        if not self.is_configured():
            log.info("usajobs_not_configured")
            return []

        try:
            headers = {
                "Authorization-Key": self._api_key,
                "User-Agent": self._email,
                "Host": "data.usajobs.gov",
            }

            params: dict[str, str | int] = {
                "Page": page,
                "ResultsPerPage": self._PAGE_SIZE,
            }

            if query:
                params["Keyword"] = query

            if location:
                params["LocationName"] = location

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self._BASE_URL,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            search_result = data.get("SearchResult", {})
            items: list[dict[str, object]] = []
            if isinstance(search_result, dict):
                raw_items = search_result.get("SearchResultItems", [])
                if isinstance(raw_items, list):
                    items = raw_items

            normalized = [self._normalize(item) for item in items]

            result_count = 0
            result_count_all = search_result.get("SearchResultCountAll", 0) if isinstance(
                search_result, dict
            ) else 0
            if isinstance(result_count_all, (int, str)):
                result_count = int(result_count_all)

            log.info(
                "usajobs_fetch_complete",
                count=len(normalized),
                query=query,
                page=page,
                total=result_count,
            )
            return normalized

        except httpx.HTTPError as exc:
            log.warning("usajobs_fetch_failed", error=str(exc))
            return []

    def _normalize(self, raw: dict[str, object]) -> NormalizedJob:
        """Normalize a USAJobs listing to common format."""
        descriptor = raw.get("MatchedObjectDescriptor", {})
        if not isinstance(descriptor, dict):
            descriptor = {}

        # Extract salary from remuneration array
        salary_min: int | None = None
        salary_max: int | None = None
        salary_currency: str | None = None
        remuneration = descriptor.get("PositionRemuneration", [])
        if isinstance(remuneration, list) and len(remuneration) > 0:
            first_rem = remuneration[0]
            if isinstance(first_rem, dict):
                salary_min = self._parse_salary(first_rem.get("MinimumRange"))
                salary_max = self._parse_salary(first_rem.get("MaximumRange"))
                salary_currency = str(first_rem.get("CurrencyCode", "USD"))

        # Extract location
        location_display = descriptor.get("PositionLocationDisplay")
        location_str: str | None = None
        if location_display:
            location_str = str(location_display)

        # Detect remote from position schedule or location
        position_schedule = descriptor.get("PositionSchedule", [])
        schedule_text = ""
        if isinstance(position_schedule, list) and len(position_schedule) > 0:
            first_schedule = position_schedule[0]
            if isinstance(first_schedule, dict):
                schedule_text = str(first_schedule.get("Name", ""))

        is_remote = (
            "remote" in (location_str or "").lower()
            or "telework" in str(descriptor.get("UserArea", "")).lower()
        )

        # Determine job type from schedule
        job_type = "full-time"
        if "part" in schedule_text.lower():
            job_type = "part-time"
        elif "intermittent" in schedule_text.lower():
            job_type = "contract"

        # Extract tags from job categories
        tags: list[str] = []
        job_category = descriptor.get("JobCategory", [])
        if isinstance(job_category, list):
            for cat in job_category:
                if isinstance(cat, dict) and cat.get("Name"):
                    tags.append(str(cat["Name"]))

        return NormalizedJob(
            external_id=str(raw.get("MatchedObjectId", "")),
            source="usajobs",
            title=str(descriptor.get("PositionTitle", "Unknown Position")),
            company=str(descriptor.get("OrganizationName", "U.S. Federal Government")),
            location=location_str,
            is_remote=is_remote,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            description=str(descriptor.get("QualificationSummary", "")),
            job_type=job_type,
            url=str(descriptor.get("PositionURI", "")),
            tags=tags,
            raw_data=raw,
            posted_at=(
                str(descriptor.get("PublicationStartDate"))
                if descriptor.get("PublicationStartDate")
                else None
            ),
        )

    def _parse_salary(self, value: object) -> int | None:
        """Parse salary value from USAJobs format to integer."""
        if value is None:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
