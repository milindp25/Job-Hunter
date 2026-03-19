from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions import NotFoundError
from app.models.job import Job
from app.models.resume import Resume
from app.models.tailored_resume import TailoredResume
from app.services.resume_tailor import ResumeTailorService

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlmodel.ext.asyncio.session import AsyncSession

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_MOCK_GEMINI_RESPONSE: dict[str, object] = {
    "tailored_summary": "Experienced software engineer specializing in backend systems.",
    "tailored_experience": [
        {
            "title": "Senior Developer",
            "company": "Acme Corp",
            "duration": "2020-2024",
            "highlights": [
                "Led development of microservices using Python and FastAPI",
                "Optimized database queries reducing latency by 40%",
            ],
        }
    ],
    "tailored_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
    "keyword_matches": ["Python", "FastAPI", "PostgreSQL"],
    "keyword_gaps": ["Kubernetes", "Terraform"],
    "match_score_before": 65,
    "match_score_after": 88,
}


async def _create_test_resume(session: AsyncSession, user_id: uuid.UUID) -> Resume:
    """Create a test resume in the database."""
    resume = Resume(
        user_id=user_id,
        filename="test_resume.pdf",
        file_size=1024,
        file_type="application/pdf",
        storage_key=f"resumes/{user_id}/test_resume.pdf",
        raw_text="Test resume content",
        parsed_data={
            "summary": "Software engineer with 5 years of experience.",
            "experience": [
                {
                    "title": "Senior Developer",
                    "company": "Acme Corp",
                    "duration": "2020-2024",
                    "highlights": [
                        "Built backend services",
                        "Improved database performance",
                    ],
                }
            ],
            "skills": ["Python", "JavaScript", "PostgreSQL", "Docker"],
        },
    )
    session.add(resume)
    await session.flush()
    return resume


async def _create_test_job(session: AsyncSession) -> Job:
    """Create a test job in the database."""
    job = Job(
        source="test",
        external_id=f"test-{uuid.uuid4().hex[:8]}",
        title="Senior Python Developer",
        company="TechCo",
        description=(
            "We are looking for a Senior Python Developer with experience in "
            "FastAPI, PostgreSQL, Docker, Kubernetes, and Terraform. "
            "You will build scalable microservices and work with cloud infrastructure."
        ),
        url="https://example.com/jobs/test",
        location="Remote",
        is_remote=True,
    )
    session.add(job)
    await session.flush()
    return job


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestResumeTailorService:
    """Tests for ResumeTailorService."""

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_tailor_resume_creates_record(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Tailoring a resume creates a new TailoredResume record."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)

        service = ResumeTailorService()
        tailored = await service.tailor_resume(
            session, str(user_id), str(resume.id), str(job.id)
        )

        assert tailored.id is not None
        assert tailored.resume_id == resume.id
        assert tailored.job_id == job.id
        assert tailored.user_id == user_id
        assert tailored.tailored_summary == (
            "Experienced software engineer specializing in backend systems."
        )
        assert len(tailored.tailored_skills) == 5
        assert tailored.match_score_before == 65
        assert tailored.match_score_after == 88
        assert tailored.ai_model == "gemini-2.0-flash"
        assert tailored.prompt_version == "v1"

        mock_generate.assert_called_once()

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_tailor_resume_not_found(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Tailoring a non-existent resume raises NotFoundError."""
        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = resp.json()["user"]["id"]

        service = ResumeTailorService()
        with pytest.raises(NotFoundError, match="Resume not found"):
            await service.tailor_resume(
                session, user_id, str(uuid.uuid4()), str(uuid.uuid4())
            )

        mock_generate.assert_not_called()

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_tailor_job_not_found(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Tailoring with a non-existent job raises NotFoundError."""
        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)

        service = ResumeTailorService()
        with pytest.raises(NotFoundError, match="Job not found"):
            await service.tailor_resume(
                session, str(user_id), str(resume.id), str(uuid.uuid4())
            )

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_tailor_preserves_original_resume(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Tailoring does not modify the original resume."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)

        original_text = resume.raw_text
        original_parsed = dict(resume.parsed_data)

        service = ResumeTailorService()
        await service.tailor_resume(
            session, str(user_id), str(resume.id), str(job.id)
        )

        await session.refresh(resume)
        assert resume.raw_text == original_text
        assert resume.parsed_data == original_parsed

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_list_tailored_resumes(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Listing tailored resumes returns user's records."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)

        service = ResumeTailorService()
        await service.tailor_resume(
            session, str(user_id), str(resume.id), str(job.id)
        )

        items = await service.list_tailored_resumes(session, str(user_id))
        assert len(items) == 1
        assert items[0].resume_id == resume.id

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_get_tailored_resume(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Getting a tailored resume by ID returns the record."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)

        service = ResumeTailorService()
        created = await service.tailor_resume(
            session, str(user_id), str(resume.id), str(job.id)
        )

        fetched = await service.get_tailored_resume(
            session, str(user_id), str(created.id)
        )
        assert fetched.id == created.id

    async def test_get_tailored_resume_wrong_user(
        self,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Getting a tailored resume with wrong user raises NotFoundError."""
        service = ResumeTailorService()
        fake_user = str(uuid.uuid4())
        with pytest.raises(NotFoundError, match="Tailored resume not found"):
            await service.get_tailored_resume(
                session, fake_user, str(uuid.uuid4())
            )

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_delete_tailored_resume(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Deleting a tailored resume removes it from the database."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)

        service = ResumeTailorService()
        created = await service.tailor_resume(
            session, str(user_id), str(resume.id), str(job.id)
        )

        await service.delete_tailored_resume(
            session, str(user_id), str(created.id)
        )

        items = await service.list_tailored_resumes(session, str(user_id))
        assert len(items) == 0

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_list_filter_by_resume_id(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """Listing with resume_id filter returns only matching records."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)

        service = ResumeTailorService()
        await service.tailor_resume(
            session, str(user_id), str(resume.id), str(job.id)
        )

        items = await service.list_tailored_resumes(
            session, str(user_id), resume_id=str(resume.id)
        )
        assert len(items) == 1

        items_empty = await service.list_tailored_resumes(
            session, str(user_id), resume_id=str(uuid.uuid4())
        )
        assert len(items_empty) == 0


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestTailoredResumesAPI:
    """Tests for tailored resumes API endpoints."""

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_post_tailor_resume(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """POST /api/v1/tailored-resumes/ creates a tailored resume."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)
        await session.commit()

        response = await client.post(
            "/api/v1/tailored-resumes/",
            json={"resume_id": str(resume.id), "job_id": str(job.id)},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["resume_id"] == str(resume.id)
        assert data["job_id"] == str(job.id)
        assert data["match_score_before"] == 65
        assert data["match_score_after"] == 88

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_get_tailored_resume_api(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """GET /api/v1/tailored-resumes/{id} returns the record."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)
        await session.commit()

        create_resp = await client.post(
            "/api/v1/tailored-resumes/",
            json={"resume_id": str(resume.id), "job_id": str(job.id)},
            headers=auth_headers,
        )
        created_id = create_resp.json()["id"]

        get_resp = await client.get(
            f"/api/v1/tailored-resumes/{created_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == created_id

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_list_tailored_resumes_api(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """GET /api/v1/tailored-resumes/ returns list with total."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)
        await session.commit()

        await client.post(
            "/api/v1/tailored-resumes/",
            json={"resume_id": str(resume.id), "job_id": str(job.id)},
            headers=auth_headers,
        )

        list_resp = await client.get(
            "/api/v1/tailored-resumes/",
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @patch("app.services.resume_tailor.generate_json", new_callable=AsyncMock)
    async def test_delete_tailored_resume_api(
        self,
        mock_generate: AsyncMock,
        session: AsyncSession,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """DELETE /api/v1/tailored-resumes/{id} removes the record."""
        mock_generate.return_value = _MOCK_GEMINI_RESPONSE

        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        user_id = uuid.UUID(resp.json()["user"]["id"])

        resume = await _create_test_resume(session, user_id)
        job = await _create_test_job(session)
        await session.commit()

        create_resp = await client.post(
            "/api/v1/tailored-resumes/",
            json={"resume_id": str(resume.id), "job_id": str(job.id)},
            headers=auth_headers,
        )
        created_id = create_resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/tailored-resumes/{created_id}",
            headers=auth_headers,
        )
        assert del_resp.status_code == 204

        get_resp = await client.get(
            f"/api/v1/tailored-resumes/{created_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404

    async def test_unauthenticated_access(
        self,
        client: AsyncClient,
    ) -> None:
        """Endpoints require authentication."""
        resp = await client.get("/api/v1/tailored-resumes/")
        assert resp.status_code == 401

    async def test_post_resume_not_found(
        self,
        auth_headers: dict[str, str],
        client: AsyncClient,
    ) -> None:
        """POST with non-existent resume returns 404."""
        response = await client.post(
            "/api/v1/tailored-resumes/",
            json={
                "resume_id": str(uuid.uuid4()),
                "job_id": str(uuid.uuid4()),
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
