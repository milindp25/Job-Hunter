from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_configured_client(
    source_name: str,
    jobs: list[dict[str, object]] | None = None,
) -> MagicMock:
    """Return a mock job-API client that reports itself as configured."""
    client = MagicMock()
    client.source_name = source_name
    client.is_configured.return_value = True
    client.fetch_jobs = AsyncMock(return_value=jobs or [])
    return client


def _mock_unconfigured_client(source_name: str = "other") -> MagicMock:
    """Return a mock job-API client that is **not** configured."""
    client = MagicMock()
    client.source_name = source_name
    client.is_configured.return_value = False
    client.fetch_jobs = AsyncMock(return_value=[])
    return client


def _sample_normalized_job(
    external_id: str = "fetch-1",
    source: str = "remoteok",
    title: str = "Fetched Job 1",
) -> dict[str, object]:
    """Return a single NormalizedJob-shaped dict for mocking fetch results."""
    return {
        "external_id": external_id,
        "source": source,
        "title": title,
        "company": "FetchCorp",
        "location": "Remote",
        "is_remote": True,
        "salary_min": 100000,
        "salary_max": 150000,
        "salary_currency": "USD",
        "description": "A fetched job",
        "job_type": "full-time",
        "url": f"https://example.com/{external_id}",
        "tags": ["python"],
        "raw_data": {},
        "posted_at": None,
    }


# ---------------------------------------------------------------------------
# Search / List jobs
# ---------------------------------------------------------------------------


class TestSearchJobs:
    """Tests for GET /api/v1/jobs (public, paginated, filterable)."""

    @pytest.mark.asyncio
    async def test_list_all_jobs(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get("/api/v1/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["jobs"]) == 3

    @pytest.mark.asyncio
    async def test_search_by_query(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get("/api/v1/jobs?query=Data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert "Data" in data["jobs"][0]["title"]

    @pytest.mark.asyncio
    async def test_filter_by_remote(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get("/api/v1/jobs?is_remote=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for job in data["jobs"]:
            assert job["is_remote"] is True

    @pytest.mark.asyncio
    async def test_filter_by_source(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get("/api/v1/jobs?source=themuse", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for job in data["jobs"]:
            assert job["source"] == "themuse"

    @pytest.mark.asyncio
    async def test_filter_by_job_type(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get("/api/v1/jobs?job_type=contract", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for job in data["jobs"]:
            assert job["job_type"] == "contract"

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get(
            "/api/v1/jobs?page=1&page_size=2", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_pagination_page_2(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get(
            "/api/v1/jobs?page=2&page_size=2", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1  # Only 1 job left on page 2

    @pytest.mark.asyncio
    async def test_public_access_no_auth(
        self,
        client: AsyncClient,
        test_jobs: list[object],
    ) -> None:
        """Jobs search should be accessible without authentication."""
        response = await client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_empty_results(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.get(
            "/api/v1/jobs?query=nonexistentjobtitle", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["jobs"] == []


# ---------------------------------------------------------------------------
# Get single job
# ---------------------------------------------------------------------------


class TestGetJob:
    """Tests for GET /api/v1/jobs/{job_id} (public)."""

    @pytest.mark.asyncio
    async def test_get_existing_job(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        response = await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["title"] == test_jobs[0].title  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get(
            f"/api/v1/jobs/{uuid.uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_public_access(
        self,
        client: AsyncClient,
        test_jobs: list[object],
    ) -> None:
        """Single job detail should be accessible without authentication."""
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        response = await client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["id"] == job_id


# ---------------------------------------------------------------------------
# Save / Unsave / List saved jobs
# ---------------------------------------------------------------------------


class TestSaveUnsaveJob:
    """Tests for POST/DELETE /api/v1/jobs/{job_id}/save and GET /api/v1/jobs/saved."""

    @pytest.mark.asyncio
    async def test_save_job(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        response = await client.post(
            f"/api/v1/jobs/{job_id}/save", headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["job"]["id"] == job_id
        assert data["notes"] is None

    @pytest.mark.asyncio
    async def test_save_with_notes(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[1].id)  # type: ignore[attr-defined]
        response = await client.post(
            f"/api/v1/jobs/{job_id}/save",
            headers=auth_headers,
            json={"notes": "Great opportunity!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["notes"] == "Great opportunity!"
        assert data["job"]["id"] == job_id

    @pytest.mark.asyncio
    async def test_save_duplicate_returns_409(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        # Save once
        first = await client.post(
            f"/api/v1/jobs/{job_id}/save", headers=auth_headers
        )
        assert first.status_code == 201
        # Try saving again
        second = await client.post(
            f"/api/v1/jobs/{job_id}/save", headers=auth_headers
        )
        assert second.status_code == 409

    @pytest.mark.asyncio
    async def test_save_nonexistent_job(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.post(
            f"/api/v1/jobs/{uuid.uuid4()}/save", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unsave_job(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        # Save first
        await client.post(f"/api/v1/jobs/{job_id}/save", headers=auth_headers)
        # Then unsave
        response = await client.delete(
            f"/api/v1/jobs/{job_id}/save", headers=auth_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_unsave_not_saved_returns_404(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        response = await client.delete(
            f"/api/v1/jobs/{job_id}/save", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_saved_jobs(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        # Save two jobs
        await client.post(
            f"/api/v1/jobs/{test_jobs[0].id}/save",  # type: ignore[attr-defined]
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/jobs/{test_jobs[1].id}/save",  # type: ignore[attr-defined]
            headers=auth_headers,
        )
        # List
        response = await client.get("/api/v1/jobs/saved", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["saved_jobs"]) == 2

    @pytest.mark.asyncio
    async def test_list_saved_jobs_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get("/api/v1/jobs/saved", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["saved_jobs"] == []

    @pytest.mark.asyncio
    async def test_save_unauthenticated(
        self,
        client: AsyncClient,
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        response = await client.post(f"/api/v1/jobs/{job_id}/save")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unsave_unauthenticated(
        self,
        client: AsyncClient,
        test_jobs: list[object],
    ) -> None:
        job_id = str(test_jobs[0].id)  # type: ignore[attr-defined]
        response = await client.delete(f"/api/v1/jobs/{job_id}/save")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_saved_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/api/v1/jobs/saved")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Fetch jobs from external sources
# ---------------------------------------------------------------------------


class TestFetchJobs:
    """Tests for POST /api/v1/jobs/fetch (authenticated, mocked API clients)."""

    @pytest.mark.asyncio
    @patch("app.services.job.USAJobsClient")
    @patch("app.services.job.AdzunaClient")
    @patch("app.services.job.TheMuseClient")
    @patch("app.services.job.RemoteOKClient")
    async def test_fetch_from_single_source(
        self,
        mock_remoteok_cls: MagicMock,
        mock_muse_cls: MagicMock,
        mock_adzuna_cls: MagicMock,
        mock_usajobs_cls: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Fetch with one configured source returning one job."""
        mock_remoteok_cls.return_value = _mock_configured_client(
            "remoteok", [_sample_normalized_job()]
        )
        mock_muse_cls.return_value = _mock_unconfigured_client("themuse")
        mock_adzuna_cls.return_value = _mock_unconfigured_client("adzuna")
        mock_usajobs_cls.return_value = _mock_unconfigured_client("usajobs")

        response = await client.post(
            "/api/v1/jobs/fetch?query=python", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "remoteok" in data["sources_fetched"]
        assert data["total_new_jobs"] == 1

    @pytest.mark.asyncio
    @patch("app.services.job.USAJobsClient")
    @patch("app.services.job.AdzunaClient")
    @patch("app.services.job.TheMuseClient")
    @patch("app.services.job.RemoteOKClient")
    async def test_fetch_from_multiple_sources(
        self,
        mock_remoteok_cls: MagicMock,
        mock_muse_cls: MagicMock,
        mock_adzuna_cls: MagicMock,
        mock_usajobs_cls: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Fetch with two configured sources returning jobs from each."""
        mock_remoteok_cls.return_value = _mock_configured_client(
            "remoteok",
            [_sample_normalized_job("r-1", "remoteok", "Remote Dev")],
        )
        mock_muse_cls.return_value = _mock_configured_client(
            "themuse",
            [_sample_normalized_job("m-1", "themuse", "Muse Dev")],
        )
        mock_adzuna_cls.return_value = _mock_unconfigured_client("adzuna")
        mock_usajobs_cls.return_value = _mock_unconfigured_client("usajobs")

        response = await client.post(
            "/api/v1/jobs/fetch?query=dev", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources_fetched"]) == 2
        assert data["total_new_jobs"] == 2

    @pytest.mark.asyncio
    @patch("app.services.job.USAJobsClient")
    @patch("app.services.job.AdzunaClient")
    @patch("app.services.job.TheMuseClient")
    @patch("app.services.job.RemoteOKClient")
    async def test_fetch_all_sources_fail_returns_500(
        self,
        mock_remoteok_cls: MagicMock,
        mock_muse_cls: MagicMock,
        mock_adzuna_cls: MagicMock,
        mock_usajobs_cls: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """When no sources are configured, the fetch should return 500."""
        for mock_cls in [mock_remoteok_cls, mock_muse_cls, mock_adzuna_cls, mock_usajobs_cls]:
            mock_cls.return_value = _mock_unconfigured_client()

        response = await client.post(
            "/api/v1/jobs/fetch?query=python", headers=auth_headers
        )
        assert response.status_code == 500

    @pytest.mark.asyncio
    @patch("app.services.job.USAJobsClient")
    @patch("app.services.job.AdzunaClient")
    @patch("app.services.job.TheMuseClient")
    @patch("app.services.job.RemoteOKClient")
    async def test_fetched_jobs_appear_in_search(
        self,
        mock_remoteok_cls: MagicMock,
        mock_muse_cls: MagicMock,
        mock_adzuna_cls: MagicMock,
        mock_usajobs_cls: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Jobs returned by fetch should be searchable via GET /api/v1/jobs."""
        mock_remoteok_cls.return_value = _mock_configured_client(
            "remoteok",
            [_sample_normalized_job("unique-42", "remoteok", "Unique Test Engineer")],
        )
        mock_muse_cls.return_value = _mock_unconfigured_client("themuse")
        mock_adzuna_cls.return_value = _mock_unconfigured_client("adzuna")
        mock_usajobs_cls.return_value = _mock_unconfigured_client("usajobs")

        fetch_resp = await client.post(
            "/api/v1/jobs/fetch?query=engineer", headers=auth_headers
        )
        assert fetch_resp.status_code == 200

        # Search for the newly fetched job
        search_resp = await client.get(
            "/api/v1/jobs?query=Unique+Test+Engineer", headers=auth_headers
        )
        assert search_resp.status_code == 200
        data = search_resp.json()
        assert data["total"] >= 1
        titles = [j["title"] for j in data["jobs"]]
        assert "Unique Test Engineer" in titles

    @pytest.mark.asyncio
    async def test_fetch_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.post("/api/v1/jobs/fetch")
        assert response.status_code == 401
