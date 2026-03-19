from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.job_clients.linkedin_apify import (
    LinkedInApifyClient,
    _build_linkedin_search_url,
    _extract_job_id,
    _is_valid_job,
    _normalize,
    _parse_salary_range,
)

# ---------------------------------------------------------------------------
# Sample Apify LinkedIn job output
# ---------------------------------------------------------------------------

def _sample_linkedin_job(**overrides: object) -> dict[str, object]:
    """Return a realistic Apify LinkedIn job result."""
    base: dict[str, object] = {
        "title": "Senior Python Developer",
        "companyName": "Acme Corp",
        "companyUrl": "https://linkedin.com/company/acme",
        "location": "San Francisco, CA",
        "description": "We are looking for a senior Python developer...",
        "jobUrl": "https://www.linkedin.com/jobs/view/3847562901/",
        "postedAt": "2026-03-15T10:00:00.000Z",
        "salary": "$120,000 - $180,000/yr",
        "contractType": "Full-time",
        "seniorityLevel": "Mid-Senior level",
        "industries": ["Technology", "Software"],
        "jobFunction": "Engineering",
        "applicationsCount": 42,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Test: _build_linkedin_search_url
# ---------------------------------------------------------------------------


class TestBuildSearchUrl:
    def test_with_query_and_location(self) -> None:
        url = _build_linkedin_search_url("python", "New York")
        assert "keywords=python" in url
        assert "location=New+York" not in url  # no URL encoding by our func
        assert "location=New York" in url
        assert "f_TPR=r604800" in url

    def test_with_query_only(self) -> None:
        url = _build_linkedin_search_url("data engineer", None)
        assert "keywords=data engineer" in url
        assert "location=" not in url

    def test_empty_query(self) -> None:
        url = _build_linkedin_search_url("", None)
        assert "keywords=" not in url
        assert "f_TPR=r604800" in url


# ---------------------------------------------------------------------------
# Test: _is_valid_job
# ---------------------------------------------------------------------------


class TestIsValidJob:
    def test_valid_job(self) -> None:
        assert _is_valid_job(_sample_linkedin_job()) is True

    def test_missing_title(self) -> None:
        assert _is_valid_job(_sample_linkedin_job(title="")) is False

    def test_missing_company(self) -> None:
        assert _is_valid_job(_sample_linkedin_job(companyName="")) is False


# ---------------------------------------------------------------------------
# Test: _extract_job_id
# ---------------------------------------------------------------------------


class TestExtractJobId:
    def test_from_standard_url(self) -> None:
        raw = {"jobUrl": "https://www.linkedin.com/jobs/view/3847562901/"}
        assert _extract_job_id(raw) == "li-3847562901"

    def test_from_url_without_trailing_slash(self) -> None:
        raw = {"jobUrl": "https://www.linkedin.com/jobs/view/3847562901"}
        assert _extract_job_id(raw) == "li-3847562901"

    def test_fallback_for_missing_url(self) -> None:
        raw = {"title": "Developer", "companyName": "Foo"}
        job_id = _extract_job_id(raw)
        assert job_id.startswith("li-")
        # Should be deterministic
        assert _extract_job_id(raw) == job_id


# ---------------------------------------------------------------------------
# Test: _parse_salary_range
# ---------------------------------------------------------------------------


class TestParseSalaryRange:
    def test_annual_range(self) -> None:
        assert _parse_salary_range("$120,000 - $180,000/yr") == (120000, 180000)

    def test_hourly_range_annualized(self) -> None:
        low, high = _parse_salary_range("$50/hr - $70/hr")
        # 50*2080 = 104000, 70*2080 = 145600
        assert low == 104000
        assert high == 145600

    def test_none_salary(self) -> None:
        assert _parse_salary_range(None) == (None, None)

    def test_non_string_salary(self) -> None:
        assert _parse_salary_range(42) == (None, None)

    def test_competitive_string(self) -> None:
        assert _parse_salary_range("Competitive") == (None, None)

    def test_empty_string(self) -> None:
        assert _parse_salary_range("") == (None, None)


# ---------------------------------------------------------------------------
# Test: _normalize
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_full_job(self) -> None:
        result = _normalize(_sample_linkedin_job())
        assert result["source"] == "linkedin"
        assert result["title"] == "Senior Python Developer"
        assert result["company"] == "Acme Corp"
        assert result["location"] == "San Francisco, CA"
        assert result["is_remote"] is False
        assert result["salary_min"] == 120000
        assert result["salary_max"] == 180000
        assert result["salary_currency"] == "USD"
        assert result["job_type"] == "full-time"
        assert result["external_id"] == "li-3847562901"
        assert "Mid-Senior level" in result["tags"]
        assert "Technology" in result["tags"]
        assert "Engineering" in result["tags"]

    def test_remote_detection_in_title(self) -> None:
        result = _normalize(_sample_linkedin_job(title="Remote Data Engineer"))
        assert result["is_remote"] is True

    def test_remote_detection_in_location(self) -> None:
        result = _normalize(_sample_linkedin_job(location="Remote"))
        assert result["is_remote"] is True

    def test_internship_job_type(self) -> None:
        result = _normalize(_sample_linkedin_job(contractType="Internship"))
        assert result["job_type"] == "internship"

    def test_contract_job_type(self) -> None:
        result = _normalize(_sample_linkedin_job(contractType="Contract"))
        assert result["job_type"] == "contract"

    def test_missing_optional_fields(self) -> None:
        minimal = {
            "title": "Developer",
            "companyName": "Foo Inc",
            "jobUrl": "https://linkedin.com/jobs/view/999999/",
        }
        result = _normalize(minimal)
        assert result["title"] == "Developer"
        assert result["company"] == "Foo Inc"
        assert result["salary_min"] is None
        assert result["tags"] == []


# ---------------------------------------------------------------------------
# Test: LinkedInApifyClient
# ---------------------------------------------------------------------------


class TestLinkedInApifyClient:
    def test_not_configured_without_key(self) -> None:
        client = LinkedInApifyClient(api_key="")
        assert client.is_configured() is False

    def test_configured_with_key(self) -> None:
        client = LinkedInApifyClient(api_key="apify_api_test_key")
        assert client.is_configured() is True

    def test_source_name(self) -> None:
        client = LinkedInApifyClient(api_key="key")
        assert client.source_name == "linkedin"

    @pytest.mark.asyncio
    async def test_returns_empty_when_not_configured(self) -> None:
        client = LinkedInApifyClient(api_key="")
        result = await client.fetch_jobs(query="python")
        assert result == []

    @pytest.mark.asyncio
    async def test_skips_page_2(self) -> None:
        client = LinkedInApifyClient(api_key="test_key")
        result = await client.fetch_jobs(query="python", page=2)
        assert result == []

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Mock a full Apify run + dataset fetch cycle."""
        client = LinkedInApifyClient(api_key="test_key")

        run_response = MagicMock()
        run_response.raise_for_status = MagicMock()
        run_response.json.return_value = {
            "data": {"defaultDatasetId": "dataset-123"},
        }

        items_response = MagicMock()
        items_response.raise_for_status = MagicMock()
        items_response.json.return_value = [
            _sample_linkedin_job(),
            _sample_linkedin_job(title="Junior Dev", companyName="Beta Inc",
                                 jobUrl="https://linkedin.com/jobs/view/111111/"),
        ]

        mock_client = AsyncMock()
        mock_client.post.return_value = run_response
        mock_client.get.return_value = items_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        target = "app.services.job_clients.linkedin_apify.httpx.AsyncClient"
        with patch(target, return_value=mock_client):
            results = await client.fetch_jobs(query="python", location="NYC")

        assert len(results) == 2
        assert results[0]["source"] == "linkedin"
        assert results[1]["title"] == "Junior Dev"

    @pytest.mark.asyncio
    async def test_handles_timeout(self) -> None:
        """Client returns empty list on timeout, doesn't crash."""
        client = LinkedInApifyClient(api_key="test_key")

        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ReadTimeout("Timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        target = "app.services.job_clients.linkedin_apify.httpx.AsyncClient"
        with patch(target, return_value=mock_client):
            results = await client.fetch_jobs(query="python")

        assert results == []

    @pytest.mark.asyncio
    async def test_handles_http_error(self) -> None:
        """Client returns empty list on HTTP errors."""
        client = LinkedInApifyClient(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Payment required", request=MagicMock(), response=mock_response,
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        target = "app.services.job_clients.linkedin_apify.httpx.AsyncClient"
        with patch(target, return_value=mock_client):
            results = await client.fetch_jobs(query="python")

        assert results == []

    @pytest.mark.asyncio
    async def test_filters_invalid_jobs(self) -> None:
        """Jobs without title or company are filtered out."""
        client = LinkedInApifyClient(api_key="test_key")

        run_response = MagicMock()
        run_response.raise_for_status = MagicMock()
        run_response.json.return_value = {
            "data": {"defaultDatasetId": "ds-1"},
        }

        items_response = MagicMock()
        items_response.raise_for_status = MagicMock()
        items_response.json.return_value = [
            _sample_linkedin_job(),
            {"title": "", "companyName": ""},  # Invalid — should be filtered
            _sample_linkedin_job(title="Valid Job", companyName="Co",
                                 jobUrl="https://linkedin.com/jobs/view/222222/"),
        ]

        mock_client = AsyncMock()
        mock_client.post.return_value = run_response
        mock_client.get.return_value = items_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        target = "app.services.job_clients.linkedin_apify.httpx.AsyncClient"
        with patch(target, return_value=mock_client):
            results = await client.fetch_jobs(query="python")

        assert len(results) == 2
