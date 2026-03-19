from __future__ import annotations

import base64
import json
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from app.models.resume import Resume

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlmodel.ext.asyncio.session import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GOOD_RAW_TEXT = """\
John Doe
john.doe@example.com
555-123-4567
123 Main Street, New York, NY 10001

Summary
Experienced software engineer with 8 years building scalable web applications.
Proficient in Python, TypeScript, React, and cloud infrastructure.

Experience
Senior Software Engineer - Acme Corp (2019-present)
- Led development of microservices handling 1M+ requests daily
- Reduced deployment time by 40% through CI/CD pipeline improvements
- Mentored team of 5 junior engineers on best practices

Software Engineer - Beta Inc (2016-2019)
- Built RESTful APIs using Python and FastAPI
- Implemented automated test suites improving code coverage to 90%
- Collaborated with product team to define technical requirements

Education
Bachelor of Science in Computer Science
State University, 2016

Skills
Python, TypeScript, React, FastAPI, PostgreSQL, Redis, Docker, Kubernetes,
CI/CD, Terraform, AWS, Git, REST APIs, Microservices

Certifications
AWS Certified Developer - Associate, 2022
"""

_GOOD_PARSED_DATA = {
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "555-123-4567",
    "skills": ["Python", "TypeScript", "React", "PostgreSQL", "Redis", "Docker"],
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Acme Corp",
            "start_date": "2019",
            "end_date": "present",
        },
        {
            "title": "Software Engineer",
            "company": "Beta Inc",
            "start_date": "2016",
            "end_date": "2019",
        },
    ],
    "education": [
        {
            "degree": "Bachelor of Science in Computer Science",
            "institution": "State University",
            "year": "2016",
        }
    ],
}


def _get_user_id_from_headers(auth_headers: dict[str, str]) -> str:
    """Decode the JWT payload (without signature verification) to extract sub."""
    token = auth_headers["Authorization"].split(" ")[1]
    # JWT payload is the second segment; pad to a multiple of 4 for base64.
    payload_b64 = token.split(".")[1]
    padding = 4 - len(payload_b64) % 4
    payload_b64 += "=" * (padding % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    return str(payload["sub"])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_resume(session: AsyncSession, auth_headers: dict[str, str]) -> Resume:
    """Create a Resume directly in the DB with ATS-friendly content."""
    user_id_str = _get_user_id_from_headers(auth_headers)
    user_uuid = uuid.UUID(user_id_str)
    now = datetime.now(UTC)

    resume = Resume(
        user_id=user_uuid,
        filename="john_doe_resume.pdf",
        file_size=50_000,
        file_type="pdf",
        storage_key=f"resumes/{user_uuid}/john_doe_resume.pdf",
        raw_text=_GOOD_RAW_TEXT,
        parsed_data=_GOOD_PARSED_DATA,
        is_primary=True,
        created_at=now,
        updated_at=now,
    )
    session.add(resume)
    await session.flush()
    return resume


@pytest_asyncio.fixture
async def test_job(session: AsyncSession) -> object:
    """Create a Job with DevOps-heavy description for ATS keyword testing."""
    from app.models.job import Job  # noqa: PLC0415

    job = Job(
        external_id="devops-test-job-ats",
        source="remoteok",
        title="Senior DevOps Engineer",
        company="TechCorp Inc",
        location="Remote",
        is_remote=True,
        salary_min=130_000,
        salary_max=180_000,
        salary_currency="USD",
        description=(
            "We are looking for a Senior DevOps Engineer with deep expertise in "
            "Kubernetes, CI/CD pipelines, and Terraform. The ideal candidate will "
            "manage cloud infrastructure on AWS, automate deployments, and drive "
            "reliability improvements across our microservices platform."
        ),
        job_type="full-time",
        url="https://example.com/jobs/devops-senior",
        tags=["kubernetes", "ci/cd", "terraform", "aws", "devops"],
        raw_data={"test": True},
        posted_at=datetime.now(UTC),
        is_active=True,
    )
    session.add(job)
    await session.flush()
    return job


# ---------------------------------------------------------------------------
# TestAtsFormatCheck
# ---------------------------------------------------------------------------


class TestAtsFormatCheck:
    """Tests for POST /api/v1/ats/check (format-only, no job_id)."""

    @pytest.mark.asyncio
    async def test_format_check_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_resume: Resume,
    ) -> None:
        """POST /ats/check without job_id returns 200 with format_only check."""
        response = await client.post(
            "/api/v1/ats/check",
            headers=auth_headers,
            json={"resume_id": str(test_resume.id)},
        )
        assert response.status_code == 200, response.text

        data = response.json()
        assert data["check_type"] == "format_only"
        assert data["resume_id"] == str(test_resume.id)
        assert data["job_id"] is None
        assert data["format_score"] >= 0
        assert data["keyword_score"] is None
        assert data["content_score"] is None
        assert isinstance(data["findings"], list)
        assert isinstance(data["overall_score"], int)

    @pytest.mark.asyncio
    async def test_format_check_unauthorized(
        self,
        client: AsyncClient,
        test_resume: Resume,
    ) -> None:
        """POST /ats/check without auth headers returns 401."""
        response = await client.post(
            "/api/v1/ats/check",
            json={"resume_id": str(test_resume.id)},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_format_check_nonexistent_resume(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """POST /ats/check with unknown resume_id returns 404."""
        response = await client.post(
            "/api/v1/ats/check",
            headers=auth_headers,
            json={"resume_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TestAtsResults
# ---------------------------------------------------------------------------


class TestAtsResults:
    """Tests for GET /api/v1/ats/results and /api/v1/ats/results/{id}."""

    @pytest.mark.asyncio
    async def test_list_results_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """GET /ats/results with no checks returns 200, empty list, total=0."""
        response = await client.get("/api/v1/ats/results", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert data["checks"] == []
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_results_unauthorized(self, client: AsyncClient) -> None:
        """GET /ats/results without auth returns 401."""
        response = await client.get("/api/v1/ats/results")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_results_after_check(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_resume: Resume,
    ) -> None:
        """After running a check, GET /ats/results returns total=1."""
        # Run a format check first
        post_resp = await client.post(
            "/api/v1/ats/check",
            headers=auth_headers,
            json={"resume_id": str(test_resume.id)},
        )
        assert post_resp.status_code == 200

        response = await client.get("/api/v1/ats/results", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["checks"]) == 1
        assert data["checks"][0]["resume_id"] == str(test_resume.id)

    @pytest.mark.asyncio
    async def test_get_result_detail(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_resume: Resume,
    ) -> None:
        """GET /ats/results/{id} returns the correct check detail."""
        # Create a check
        post_resp = await client.post(
            "/api/v1/ats/check",
            headers=auth_headers,
            json={"resume_id": str(test_resume.id)},
        )
        assert post_resp.status_code == 200
        check_id = post_resp.json()["id"]

        response = await client.get(
            f"/api/v1/ats/results/{check_id}", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == check_id
        assert data["check_type"] == "format_only"
        assert data["resume_id"] == str(test_resume.id)
        assert isinstance(data["findings"], list)

    @pytest.mark.asyncio
    async def test_get_result_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """GET /ats/results/{random_uuid} returns 404."""
        response = await client.get(
            f"/api/v1/ats/results/{uuid.uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404

        error = response.json()
        assert error["error"]["code"] == "ATS_CHECK_NOT_FOUND"


# ---------------------------------------------------------------------------
# TestAtsDismiss
# ---------------------------------------------------------------------------


class TestAtsDismiss:
    """Tests for PATCH /api/v1/ats/results/{check_id}/findings/{finding_id}/dismiss."""

    @pytest.mark.asyncio
    async def test_dismiss_finding(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_resume: Resume,
    ) -> None:
        """POST a format check, then dismiss first finding, verify dismissed=True."""
        # Run format check
        post_resp = await client.post(
            "/api/v1/ats/check",
            headers=auth_headers,
            json={"resume_id": str(test_resume.id)},
        )
        assert post_resp.status_code == 200
        check_data = post_resp.json()
        check_id = check_data["id"]
        findings = check_data["findings"]

        if not findings:
            pytest.skip("No findings produced by this resume — cannot test dismiss")

        first_finding_id = findings[0]["id"]

        # Dismiss it
        dismiss_resp = await client.patch(
            f"/api/v1/ats/results/{check_id}/findings/{first_finding_id}/dismiss",
            headers=auth_headers,
            json={"dismissed": True},
        )
        assert dismiss_resp.status_code == 200

        updated = dismiss_resp.json()
        dismissed_finding = next(
            (f for f in updated["findings"] if f["id"] == first_finding_id), None
        )
        assert dismissed_finding is not None
        assert dismissed_finding["dismissed"] is True

    @pytest.mark.asyncio
    async def test_undismiss_finding(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_resume: Resume,
    ) -> None:
        """Dismiss then undismiss a finding; verify dismissed toggles correctly."""
        post_resp = await client.post(
            "/api/v1/ats/check",
            headers=auth_headers,
            json={"resume_id": str(test_resume.id)},
        )
        assert post_resp.status_code == 200
        check_id = post_resp.json()["id"]
        findings = post_resp.json()["findings"]

        if not findings:
            pytest.skip("No findings produced — cannot test undismiss")

        finding_id = findings[0]["id"]

        # Dismiss
        await client.patch(
            f"/api/v1/ats/results/{check_id}/findings/{finding_id}/dismiss",
            headers=auth_headers,
            json={"dismissed": True},
        )

        # Undismiss
        resp = await client.patch(
            f"/api/v1/ats/results/{check_id}/findings/{finding_id}/dismiss",
            headers=auth_headers,
            json={"dismissed": False},
        )
        assert resp.status_code == 200

        updated_finding = next(
            (f for f in resp.json()["findings"] if f["id"] == finding_id), None
        )
        assert updated_finding is not None
        assert updated_finding["dismissed"] is False

    @pytest.mark.asyncio
    async def test_dismiss_unauthorized(
        self,
        client: AsyncClient,
        test_resume: Resume,
    ) -> None:
        """PATCH dismiss endpoint without auth returns 401."""
        response = await client.patch(
            f"/api/v1/ats/results/{uuid.uuid4()}/findings/{uuid.uuid4()}/dismiss",
            json={"dismissed": True},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# TestAtsFullCheck
# ---------------------------------------------------------------------------


class TestAtsFullCheck:
    """Tests for full check (with job_id) behaviour."""

    @pytest.mark.asyncio
    async def test_full_check_requires_consent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_resume: Resume,
        test_job: object,
    ) -> None:
        """POST /ats/check with job_id returns 403 ATS_CONSENT_REQUIRED.

        A freshly-registered user has not consented to AI analysis, so the
        full-check path must raise AtsConsentRequiredError before calling Gemini.
        """
        job_id = str(test_job.id)  # type: ignore[attr-defined]
        response = await client.post(
            "/api/v1/ats/check",
            headers=auth_headers,
            json={"resume_id": str(test_resume.id), "job_id": job_id},
        )
        assert response.status_code == 403

        error = response.json()
        assert error["error"]["code"] == "ATS_CONSENT_REQUIRED"

    @pytest.mark.asyncio
    async def test_full_check_unauthorized(
        self,
        client: AsyncClient,
        test_resume: Resume,
        test_job: object,
    ) -> None:
        """POST /ats/check with job_id but no auth returns 401."""
        response = await client.post(
            "/api/v1/ats/check",
            json={
                "resume_id": str(test_resume.id),
                "job_id": str(test_job.id),  # type: ignore[attr-defined]
            },
        )
        assert response.status_code == 401
