from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.services.gemini import GeminiMatchResult
from app.services.keyword_matcher import calculate_keyword_match


# ---------------------------------------------------------------------------
# TestKeywordMatcher — unit tests, no HTTP, no DB
# ---------------------------------------------------------------------------


class TestKeywordMatcher:
    """Unit tests for the Layer 1 keyword matcher."""

    def test_high_skill_match(self) -> None:
        """User skills match job tags -> high skills score."""
        result = calculate_keyword_match(
            user_skills=[{"name": "Python", "level": "advanced", "years": 5}],
            user_desired_roles=["Software Engineer"],
            user_desired_locations=["Remote"],
            user_min_salary=100000,
            user_years_of_experience=5,
            job_title="Senior Python Developer",
            job_description="Looking for Python developer with 3+ years experience",
            job_tags=["python", "django", "fastapi"],
            job_location="Remote",
            job_is_remote=True,
            job_salary_min=120000,
            job_salary_max=160000,
        )
        assert result.skills_score > 50
        assert result.overall_score > 50

    def test_no_skill_overlap(self) -> None:
        """User skills don't match job tags -> low scores."""
        result = calculate_keyword_match(
            user_skills=[{"name": "Java", "level": "expert", "years": 10}],
            user_desired_roles=["Java Developer"],
            user_desired_locations=["Remote"],
            user_min_salary=100000,
            user_years_of_experience=10,
            job_title="iOS Developer",
            job_description="Looking for Swift developer",
            job_tags=["swift", "ios", "xcode"],
            job_location="San Francisco",
            job_is_remote=False,
            job_salary_min=80000,
            job_salary_max=120000,
        )
        assert result.skills_score == 0
        assert result.overall_score < 40

    def test_remote_location_match(self) -> None:
        """User wants remote, job is remote -> location score 100."""
        result = calculate_keyword_match(
            user_skills=[{"name": "Python", "level": "intermediate", "years": 2}],
            user_desired_roles=[],
            user_desired_locations=["Remote"],
            user_min_salary=None,
            user_years_of_experience=None,
            job_title="Developer",
            job_description="Remote position",
            job_tags=["python"],
            job_location=None,
            job_is_remote=True,
            job_salary_min=None,
            job_salary_max=None,
        )
        assert result.location_score == 100

    def test_salary_below_minimum(self) -> None:
        """Job salary max is well below user minimum -> low salary score."""
        result = calculate_keyword_match(
            user_skills=[],
            user_desired_roles=[],
            user_desired_locations=[],
            user_min_salary=150000,
            user_years_of_experience=None,
            job_title="Developer",
            job_description="Entry level position",
            job_tags=[],
            job_location=None,
            job_is_remote=False,
            job_salary_min=40000,
            job_salary_max=60000,
        )
        assert result.salary_score < 30

    def test_role_match(self) -> None:
        """Desired role contained in job title -> high role score."""
        result = calculate_keyword_match(
            user_skills=[],
            user_desired_roles=["Software Engineer"],
            user_desired_locations=[],
            user_min_salary=None,
            user_years_of_experience=None,
            job_title="Senior Software Engineer",
            job_description="We need an engineer",
            job_tags=[],
            job_location=None,
            job_is_remote=False,
            job_salary_min=None,
            job_salary_max=None,
        )
        assert result.role_score > 70

    def test_empty_data_returns_neutral(self) -> None:
        """With no user data, scores should be neutral and within 0-100."""
        result = calculate_keyword_match(
            user_skills=[],
            user_desired_roles=[],
            user_desired_locations=[],
            user_min_salary=None,
            user_years_of_experience=None,
            job_title="Developer",
            job_description="A job",
            job_tags=[],
            job_location=None,
            job_is_remote=False,
            job_salary_min=None,
            job_salary_max=None,
        )
        assert 0 <= result.overall_score <= 100


# ---------------------------------------------------------------------------
# TestBulkAnalyze — API tests for POST /matching/analyze
# ---------------------------------------------------------------------------


class TestBulkAnalyze:
    """Tests for POST /api/v1/matching/analyze (bulk keyword matching)."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/matching/analyze")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_incomplete_profile(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """User has no skills -> should fail with 400."""
        response = await client.post(
            "/api/v1/matching/analyze", headers=auth_headers
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_analyze_with_profile(
        self,
        client: AsyncClient,
        auth_headers_with_profile: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        response = await client.post(
            "/api/v1/matching/analyze", headers=auth_headers_with_profile
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs_analyzed"] > 0
        assert "message" in data

    @pytest.mark.asyncio
    async def test_analyze_creates_match_results(
        self,
        client: AsyncClient,
        auth_headers_with_profile: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        # Analyze
        await client.post(
            "/api/v1/matching/analyze", headers=auth_headers_with_profile
        )
        # Check results exist
        response = await client.get(
            "/api/v1/matching/results", headers=auth_headers_with_profile
        )
        assert response.status_code == 200
        assert response.json()["total"] > 0


# ---------------------------------------------------------------------------
# TestMatchResults — API tests for GET /matching/results
# ---------------------------------------------------------------------------


class TestMatchResults:
    """Tests for GET /api/v1/matching/results (paginated match listing)."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/matching/results")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_results(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(
            "/api/v1/matching/results", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_sorted_by_score(
        self,
        client: AsyncClient,
        auth_headers_with_profile: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        await client.post(
            "/api/v1/matching/analyze", headers=auth_headers_with_profile
        )
        response = await client.get(
            "/api/v1/matching/results", headers=auth_headers_with_profile
        )
        matches = response.json()["matches"]
        if len(matches) > 1:
            scores = [m["match"]["overall_score"] for m in matches]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        client: AsyncClient,
        auth_headers_with_profile: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        await client.post(
            "/api/v1/matching/analyze", headers=auth_headers_with_profile
        )
        response = await client.get(
            "/api/v1/matching/results?page=1&page_size=1",
            headers=auth_headers_with_profile,
        )
        assert response.status_code == 200
        assert len(response.json()["matches"]) <= 1


# ---------------------------------------------------------------------------
# TestMatchDetail — API tests for GET /matching/results/{job_id}
# ---------------------------------------------------------------------------


class TestMatchDetail:
    """Tests for GET /api/v1/matching/results/{job_id}."""

    @pytest.mark.asyncio
    async def test_get_match_detail(
        self,
        client: AsyncClient,
        auth_headers_with_profile: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        await client.post(
            "/api/v1/matching/analyze", headers=auth_headers_with_profile
        )
        results = await client.get(
            "/api/v1/matching/results", headers=auth_headers_with_profile
        )
        if results.json()["total"] > 0:
            job_id = results.json()["matches"][0]["match"]["job_id"]
            response = await client.get(
                f"/api/v1/matching/results/{job_id}",
                headers=auth_headers_with_profile,
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_nonexistent_match(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(
            f"/api/v1/matching/results/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TestSingleAnalyze — API tests for POST /matching/analyze/{job_id}
# ---------------------------------------------------------------------------


class TestSingleAnalyze:
    """Tests for POST /api/v1/matching/analyze/{job_id} (deep analysis)."""

    @pytest.mark.asyncio
    @patch("app.services.matching.gemini_service")
    async def test_with_gemini(
        self,
        mock_gemini: object,
        client: AsyncClient,
        auth_headers_with_profile: dict[str, str],
        test_jobs: list[object],
    ) -> None:
        mock_gemini.is_gemini_configured.return_value = True  # type: ignore[attr-defined]
        mock_gemini.analyze_job_match = AsyncMock(  # type: ignore[attr-defined]
            return_value=GeminiMatchResult(
                overall_score=85,
                skills_match=90,
                experience_match=80,
                education_match=70,
                location_match=100,
                salary_match=85,
                strengths=["Strong Python skills"],
                gaps=["No cloud experience"],
                recommendation="Good Match",
            )
        )
        # Run bulk first to create keyword match
        await client.post(
            "/api/v1/matching/analyze", headers=auth_headers_with_profile
        )
        results = await client.get(
            "/api/v1/matching/results", headers=auth_headers_with_profile
        )
        if results.json()["total"] > 0:
            job_id = results.json()["matches"][0]["match"]["job_id"]
            response = await client.post(
                f"/api/v1/matching/analyze/{job_id}",
                headers=auth_headers_with_profile,
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            f"/api/v1/matching/analyze/{uuid.uuid4()}"
        )
        assert response.status_code == 401
