from __future__ import annotations

import httpx
import structlog

from app.services.job_clients.base import NormalizedJob

log = structlog.get_logger()

# Default actor — curious_coder's LinkedIn Jobs Scraper (free with Apify credits).
# The bebity actor ($29.99/month) is popular but paid-only after a 3-day trial.
# Users can override via APIFY_LINKEDIN_ACTOR_ID env var.
# NOTE: Apify API uses tilde (~) between username and actor name in URLs,
# not slash (/). The store shows "user/actor" but the API needs "user~actor".
_DEFAULT_ACTOR_ID = "curious_coder~linkedin-jobs-scraper"

_APIFY_BASE_URL = "https://api.apify.com/v2"

# Maximum time (seconds) to wait for the actor run to finish.
# Apify's synchronous mode blocks the POST call until the run completes
# or this timeout is reached. LinkedIn scraping typically takes 10-30s.
_WAIT_FOR_FINISH_SECS = 60


class LinkedInApifyClient:
    """Client for LinkedIn job scraping via Apify actors.

    Unlike the other job clients that hit free REST APIs directly, this one
    delegates scraping to an Apify actor. Apify runs a headless browser to
    scrape LinkedIn search results, normalizing them into structured JSON.

    Cost: ~$0.25-0.50 per run on Apify's pay-as-you-go model.
    Free tier gives $5/month ≈ 10-20 scrapes. Use sparingly.
    """

    source_name: str = "linkedin"

    def __init__(self, api_key: str, actor_id: str = _DEFAULT_ACTOR_ID) -> None:
        self._api_key = api_key
        self._actor_id = actor_id

    def is_configured(self) -> bool:
        """Check if the Apify API key is provided."""
        return bool(self._api_key)

    async def fetch_jobs(
        self,
        query: str = "",
        location: str | None = None,
        page: int = 1,
    ) -> list[NormalizedJob]:
        """Run the Apify LinkedIn Jobs Scraper and return normalized results.

        Uses Apify's synchronous execution mode: the POST request blocks until
        the actor run finishes (up to ``_WAIT_FOR_FINISH_SECS``), then we read
        the dataset items from the response.

        Only fetches page 1 — Apify actors don't support traditional pagination.
        Subsequent pages are silently skipped to avoid burning compute credits.
        """
        if not self.is_configured():
            log.info("linkedin_apify_not_configured")
            return []

        # Only fetch page 1 — Apify runs are expensive, no traditional pagination
        if page > 1:
            return []

        try:
            run_url = (
                f"{_APIFY_BASE_URL}/acts/{self._actor_id}/runs"
                f"?waitForFinish={_WAIT_FOR_FINISH_SECS}"
            )
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }

            # Actor input — matches the curious_coder/linkedin-jobs-scraper schema.
            # This actor accepts a `urls` array and `maxItems` count.
            actor_input: dict[str, object] = {
                "urls": [_build_linkedin_search_url(query, location)],
                "maxItems": 20,
            }

            async with httpx.AsyncClient(timeout=90.0) as client:
                # Step 1: Run the actor (synchronous mode waits for completion)
                run_response = await client.post(
                    run_url,
                    headers=headers,
                    json=actor_input,
                )
                run_response.raise_for_status()
                run_data = run_response.json()

                dataset_id = run_data.get("data", {}).get("defaultDatasetId")
                if not dataset_id:
                    log.warning("linkedin_apify_no_dataset", run_data=run_data)
                    return []

                # Step 2: Fetch the dataset items (the actual job listings)
                items_url = f"{_APIFY_BASE_URL}/datasets/{dataset_id}/items"
                items_response = await client.get(items_url, headers=headers)
                items_response.raise_for_status()
                items: list[dict[str, object]] = items_response.json()

            normalized = [_normalize(job) for job in items if _is_valid_job(job)]
            log.info(
                "linkedin_apify_fetch_complete",
                count=len(normalized),
                raw_count=len(items),
                query=query,
                location=location,
            )
            return normalized

        except httpx.TimeoutException:
            log.warning(
                "linkedin_apify_timeout",
                query=query,
                timeout=_WAIT_FOR_FINISH_SECS,
            )
            return []
        except httpx.HTTPStatusError as exc:
            log.warning(
                "linkedin_apify_http_error",
                status=exc.response.status_code,
                error=str(exc),
            )
            return []
        except httpx.HTTPError as exc:
            log.warning("linkedin_apify_fetch_failed", error=str(exc))
            return []


def _build_linkedin_search_url(query: str, location: str | None) -> str:
    """Build a LinkedIn job search URL from query parameters.

    The actor accepts a full LinkedIn search URL as input rather than
    separate query/location fields. This matches how users would search
    on LinkedIn itself.
    """
    base = "https://www.linkedin.com/jobs/search/?"
    params: list[str] = []
    if query:
        params.append(f"keywords={query}")
    if location:
        params.append(f"location={location}")
    # Default to recent postings (past week) to keep results fresh
    params.append("f_TPR=r604800")
    return base + "&".join(params)


def _is_valid_job(raw: dict[str, object]) -> bool:
    """Filter out incomplete results that lack essential fields."""
    return bool(raw.get("title") and raw.get("companyName"))


def _normalize(raw: dict[str, object]) -> NormalizedJob:
    """Normalize a LinkedIn job from Apify output to our common format.

    Actual curious_coder actor output fields (verified via live test):
        id, title, companyName, companyLinkedinUrl, companyLogo,
        location, link, descriptionText, descriptionHtml, postedAt,
        salary, salaryInsights, employmentType, seniorityLevel,
        industries, jobFunction, applicantsCount, workRemoteAllowed,
        workplaceTypes, country, expireAt, postedAtTimestamp
    """
    # --- Tag assembly: include seniority + industries + jobFunction ---
    tags: list[str] = []
    seniority = str(raw.get("seniorityLevel", "")).strip()
    if seniority:
        tags.append(seniority)
    industries = raw.get("industries")
    if isinstance(industries, list):
        tags.extend(str(ind) for ind in industries if ind)
    job_function = str(raw.get("jobFunction", "")).strip()
    if job_function:
        tags.append(job_function)

    # --- Location & remote detection ---
    location_str = str(raw.get("location", "")).strip() or None
    title = str(raw.get("title", "Unknown Position"))
    # Prefer the explicit workRemoteAllowed flag from LinkedIn
    is_remote = bool(raw.get("workRemoteAllowed")) or any(
        "remote" in (s or "").lower()
        for s in (title, location_str)
    )

    # --- Salary parsing ---
    salary_min, salary_max = _parse_salary_range(raw.get("salary"))

    # --- Job type from employmentType (curious_coder field name) ---
    employment = str(raw.get("employmentType", "")).lower()
    if "part" in employment:
        job_type = "part-time"
    elif "contract" in employment or "temporary" in employment:
        job_type = "contract"
    elif "intern" in employment:
        job_type = "internship"
    else:
        job_type = "full-time"

    # --- Description: prefer plain text, fall back to HTML ---
    description = str(raw.get("descriptionText", ""))
    if not description:
        description = str(raw.get("description", ""))

    # --- URL: curious_coder uses "link", bebity uses "jobUrl" ---
    job_url = str(raw.get("link") or raw.get("jobUrl") or "")

    return NormalizedJob(
        external_id=_extract_job_id(raw),
        source="linkedin",
        title=title,
        company=str(raw.get("companyName", "Unknown Company")),
        location=location_str,
        is_remote=is_remote,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD" if (salary_min or salary_max) else None,
        description=description,
        job_type=job_type,
        url=job_url,
        tags=tags,
        raw_data=raw,
        posted_at=str(raw.get("postedAt")) if raw.get("postedAt") else None,
    )


def _extract_job_id(raw: dict[str, object]) -> str:
    """Extract a stable job ID from the LinkedIn job URL or raw data.

    LinkedIn job URLs contain a numeric ID: .../view/1234567890/
    We prefer this over Apify's internal IDs for deduplication.
    """
    # Try the direct LinkedIn numeric ID first (curious_coder provides "id")
    raw_id = str(raw.get("id", ""))
    if raw_id.isdigit() and len(raw_id) >= 6:
        return f"li-{raw_id}"

    # Try extracting from URL (link or jobUrl field)
    job_url = str(raw.get("link") or raw.get("jobUrl") or "")
    for segment in job_url.rstrip("/").split("/"):
        if segment.isdigit() and len(segment) >= 6:
            return f"li-{segment}"

    # Fallback to title+company hash
    fallback = f'{raw.get("title")}-{raw.get("companyName")}'
    return f"li-{hash(fallback) & 0xFFFFFFFF}"


def _parse_salary_range(salary: object) -> tuple[int | None, int | None]:
    """Parse LinkedIn salary string into min/max integers.

    LinkedIn salary formats vary: "$80,000 - $120,000/yr",
    "$50/hr - $70/hr", "Competitive", etc.
    """
    if not salary or not isinstance(salary, str):
        return None, None

    # Remove common decorators
    cleaned = salary.replace(",", "").replace("$", "").replace("/yr", "").replace("/hr", "")

    parts = cleaned.split("-")
    if len(parts) == 2:
        try:
            low = int(float(parts[0].strip()))
            high = int(float(parts[1].strip()))
            # If hourly (small numbers), annualize
            if low < 500:
                low *= 2080
                high *= 2080
            return low, high
        except (ValueError, TypeError):
            return None, None

    return None, None
