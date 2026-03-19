from __future__ import annotations

import re
from typing import TYPE_CHECKING

import httpx
import structlog

from app.services.user import update_profile

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()


def _clean_linkedin_url(url: str) -> str:
    """Normalize a LinkedIn profile URL."""
    url = url.strip().rstrip("/")
    # Ensure it's a LinkedIn profile URL
    if "linkedin.com/in/" not in url:
        raise ValueError("Invalid LinkedIn profile URL. Expected format: https://www.linkedin.com/in/username")
    return url


async def import_linkedin_profile(
    session: AsyncSession,
    user_id: str,
    linkedin_url: str,
) -> dict[str, str | list[str] | None]:
    """Import profile data from a LinkedIn public profile URL.

    This is a best-effort operation using Open Graph meta tags and
    JSON-LD structured data from LinkedIn's public profile pages.
    LinkedIn may block or limit access.

    Args:
        session: Database session
        user_id: The user's ID
        linkedin_url: LinkedIn profile URL

    Returns:
        Dict of extracted profile fields that were saved.
    """
    clean_url = _clean_linkedin_url(linkedin_url)

    extracted: dict[str, str | list[str] | None] = {}

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=10.0,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; JobHunter/1.0)",
                "Accept": "text/html",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            response = await client.get(clean_url)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as exc:
        log.warning("linkedin_fetch_failed", url=clean_url, error=str(exc))
        return extracted  # Return empty — best effort

    # Extract from Open Graph meta tags
    og_title = _extract_meta(html, "og:title")
    og_description = _extract_meta(html, "og:description")
    og_image = _extract_meta(html, "og:image")

    if og_title:
        # LinkedIn og:title format: "Name - Title - Company | LinkedIn"
        parts = og_title.split(" - ")
        if parts:
            extracted["full_name"] = parts[0].strip()
            if len(parts) >= 2:
                extracted["headline"] = parts[1].strip()

    if og_description:
        # Usually contains a summary snippet
        extracted["summary_snippet"] = og_description.strip()

    if og_image and "media.licdn.com" in og_image:
        extracted["avatar_url"] = og_image

    # Save extracted data to profile
    profile_data: dict[str, str | int | list[str] | list[dict[str, str]] | bool | None] = {}

    if "summary_snippet" in extracted and extracted["summary_snippet"]:
        profile_data["summary"] = str(extracted["summary_snippet"])

    # Always save the LinkedIn URL
    profile_data["linkedin_url"] = clean_url

    if profile_data:
        await update_profile(session, user_id, profile_data)
        log.info("linkedin_profile_imported", user_id=user_id, fields=list(profile_data.keys()))

    return extracted


def _extract_meta(html: str, property_name: str) -> str | None:
    """Extract content from an Open Graph meta tag."""
    pattern = rf'<meta\s+(?:property|name)="{re.escape(property_name)}"\s+content="([^"]*)"'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1)
    # Try reversed attribute order
    pattern2 = rf'content="([^"]*)"\s+(?:property|name)="{re.escape(property_name)}"'
    match2 = re.search(pattern2, html, re.IGNORECASE)
    if match2:
        return match2.group(1)
    return None
