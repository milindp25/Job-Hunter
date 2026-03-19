from __future__ import annotations

import html

import httpx
import structlog

from app.services.job_clients.base import NormalizedJob

log = structlog.get_logger()


class TheMuseClient:
    """Client for The Muse public job board API.

    The Muse offers a free, unauthenticated API with server-side pagination.
    Results include company info, locations, and HTML job descriptions.
    """

    source_name: str = "themuse"

    _BASE_URL: str = "https://www.themuse.com/api/public/jobs"

    def is_configured(self) -> bool:
        """The Muse requires no API key."""
        return True

    async def fetch_jobs(
        self,
        query: str = "",
        location: str | None = None,
        page: int = 1,
    ) -> list[NormalizedJob]:
        """Fetch jobs from The Muse API.

        The Muse uses 0-indexed pages internally, so we convert
        from our 1-indexed page parameter.
        """
        try:
            params: dict[str, str | int] = {
                "page": page - 1,  # The Muse uses 0-indexed pages
            }

            if query:
                params["category"] = query

            if location:
                params["location"] = location

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self._BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

            results: list[dict[str, object]] = data.get("results", [])
            normalized = [self._normalize(job) for job in results]
            log.info(
                "themuse_fetch_complete",
                count=len(normalized),
                query=query,
                page=page,
                total_pages=data.get("page_count", 0),
            )
            return normalized

        except httpx.HTTPError as exc:
            log.warning("themuse_fetch_failed", error=str(exc))
            return []

    def _normalize(self, raw: dict[str, object]) -> NormalizedJob:
        """Normalize a Muse job to common format."""
        # Extract nested company name
        company_data = raw.get("company", {})
        company_name = "Unknown Company"
        if isinstance(company_data, dict):
            company_name = str(company_data.get("name", "Unknown Company"))

        # Extract first location name
        locations_data = raw.get("locations", [])
        location_str: str | None = None
        is_remote = False
        if isinstance(locations_data, list) and len(locations_data) > 0:
            first_loc = locations_data[0]
            if isinstance(first_loc, dict):
                loc_name = str(first_loc.get("name", ""))
                location_str = loc_name or None
                is_remote = "remote" in loc_name.lower() if loc_name else False

        # Extract seniority level
        levels_data = raw.get("levels", [])
        job_type = "full-time"
        if isinstance(levels_data, list) and len(levels_data) > 0:
            first_level = levels_data[0]
            if isinstance(first_level, dict):
                level_name = str(first_level.get("name", "")).lower()
                if "intern" in level_name:
                    job_type = "internship"

        # Extract category tags
        categories_data = raw.get("categories", [])
        tags: list[str] = []
        if isinstance(categories_data, list):
            for cat in categories_data:
                if isinstance(cat, dict) and cat.get("name"):
                    tags.append(str(cat["name"]))

        # Extract URL from refs
        refs_data = raw.get("refs", {})
        url = ""
        if isinstance(refs_data, dict):
            url = str(refs_data.get("landing_page", ""))

        # Clean HTML from description
        contents = str(raw.get("contents", ""))
        description = self._strip_html(contents)

        return NormalizedJob(
            external_id=str(raw.get("id", "")),
            source="themuse",
            title=str(raw.get("name", "Unknown Position")),
            company=company_name,
            location=location_str,
            is_remote=is_remote,
            salary_min=None,  # The Muse does not provide salary data
            salary_max=None,
            salary_currency=None,
            description=description,
            job_type=job_type,
            url=url,
            tags=tags,
            raw_data=raw,
            posted_at=str(raw.get("publication_date")) if raw.get("publication_date") else None,
        )

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags and decode HTML entities from text."""
        # Decode HTML entities first (e.g., &amp; -> &)
        decoded = html.unescape(text)
        # Simple tag stripping — remove anything between < and >
        result: list[str] = []
        in_tag = False
        for char in decoded:
            if char == "<":
                in_tag = True
            elif char == ">":
                in_tag = False
            elif not in_tag:
                result.append(char)
        return "".join(result).strip()
