from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.models.resume import Resume
from app.models.user import User, UserProfile
from app.services.resume_generator import ResumeGeneratorService
from app.utils.security import hash_password


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user_with_resume(session: AsyncSession) -> tuple[User, Resume]:
    """Create a test user, profile, and resume."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="gen@example.com",
        full_name="Generator Test",
        hashed_password=hash_password("password123"),
    )
    session.add(user)

    profile = UserProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        phone="555-0000",
        location="New York, NY",
        linkedin_url="https://linkedin.com/in/gentest",
        summary="Test summary from profile.",
        skills=[{"name": "Python", "level": "Advanced"}],
        languages=[{"name": "English"}],
        certifications=["AWS Cert"],
    )
    session.add(profile)

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        filename="test.pdf",
        file_size=1024,
        file_type="application/pdf",
        storage_key=f"resumes/{user_id}/test.pdf",
        parsed_data={
            "full_name": "Generator Test",
            "email": "gen@example.com",
            "summary": "Parsed resume summary.",
            "skills": ["Python", "FastAPI", "React"],
            "experience": [
                {
                    "title": "Engineer",
                    "company": "TestCo",
                    "dates": "2022 - Present",
                    "description": "Built APIs.",
                }
            ],
            "education": [
                {
                    "degree": "B.S. CS",
                    "school": "State University",
                    "dates": "2018 - 2022",
                }
            ],
            "certifications": ["AWS SAA"],
        },
    )
    session.add(resume)
    await session.flush()

    return user, resume


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestResumeGeneratorService:
    async def test_generate_pdf_classic(
        self,
        session: AsyncSession,
        user_with_resume: tuple[User, Resume],
    ) -> None:
        user, resume = user_with_resume
        service = ResumeGeneratorService()
        pdf = await service.generate_pdf(
            session=session,
            user_id=user.id,
            resume_id=resume.id,
            template_id="classic",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    async def test_generate_pdf_modern(
        self,
        session: AsyncSession,
        user_with_resume: tuple[User, Resume],
    ) -> None:
        user, resume = user_with_resume
        service = ResumeGeneratorService()
        pdf = await service.generate_pdf(
            session=session,
            user_id=user.id,
            resume_id=resume.id,
            template_id="modern",
        )
        assert pdf[:5] == b"%PDF-"

    async def test_generate_pdf_minimal(
        self,
        session: AsyncSession,
        user_with_resume: tuple[User, Resume],
    ) -> None:
        user, resume = user_with_resume
        service = ResumeGeneratorService()
        pdf = await service.generate_pdf(
            session=session,
            user_id=user.id,
            resume_id=resume.id,
            template_id="minimal",
        )
        assert pdf[:5] == b"%PDF-"

    async def test_generate_pdf_with_accent_color(
        self,
        session: AsyncSession,
        user_with_resume: tuple[User, Resume],
    ) -> None:
        user, resume = user_with_resume
        service = ResumeGeneratorService()
        pdf = await service.generate_pdf(
            session=session,
            user_id=user.id,
            resume_id=resume.id,
            template_id="classic",
            accent_color="#E11D48",
        )
        assert pdf[:5] == b"%PDF-"

    async def test_unknown_template_raises_validation_error(
        self,
        session: AsyncSession,
        user_with_resume: tuple[User, Resume],
    ) -> None:
        user, resume = user_with_resume
        service = ResumeGeneratorService()
        with pytest.raises(ValidationError, match="Unknown template"):
            await service.generate_pdf(
                session=session,
                user_id=user.id,
                resume_id=resume.id,
                template_id="nonexistent",
            )

    async def test_missing_resume_raises_not_found(
        self,
        session: AsyncSession,
        user_with_resume: tuple[User, Resume],
    ) -> None:
        user, _resume = user_with_resume
        service = ResumeGeneratorService()
        with pytest.raises(NotFoundError, match="Resume not found"):
            await service.generate_pdf(
                session=session,
                user_id=user.id,
                resume_id=uuid.uuid4(),
                template_id="classic",
            )

    async def test_wrong_user_raises_not_found(
        self,
        session: AsyncSession,
        user_with_resume: tuple[User, Resume],
    ) -> None:
        _user, resume = user_with_resume
        service = ResumeGeneratorService()
        with pytest.raises(NotFoundError, match="Resume not found"):
            await service.generate_pdf(
                session=session,
                user_id=uuid.uuid4(),
                resume_id=resume.id,
                template_id="classic",
            )


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestResumeEndpoints:
    async def test_list_templates_endpoint(self, client: object) -> None:
        response = await client.get("/api/v1/resumes/templates")  # type: ignore[union-attr]
        assert response.status_code == 200  # type: ignore[union-attr]
        data = response.json()  # type: ignore[union-attr]
        assert "templates" in data
        assert len(data["templates"]) == 3
        ids = {t["id"] for t in data["templates"]}
        assert ids == {"classic", "modern", "minimal"}

    async def test_generate_requires_auth(self, client: object) -> None:
        fake_id = str(uuid.uuid4())
        response = await client.get(  # type: ignore[union-attr]
            f"/api/v1/resumes/{fake_id}/generate"
        )
        assert response.status_code == 401  # type: ignore[union-attr]
