from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlmodel import select

from app.exceptions import NotFoundError, ValidationError
from app.models.resume import Resume
from app.models.user import User, UserProfile
from app.services.resume_templates import ResumeData, TemplateRegistry

if TYPE_CHECKING:
    import uuid

    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()


class ResumeGeneratorService:
    """Generates PDF resumes from stored resume data and user profiles."""

    async def generate_pdf(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        template_id: str = "classic",
        accent_color: str | None = None,
    ) -> bytes:
        """Render a resume as a PDF using the chosen template.

        Args:
            session: Async database session.
            user_id: Authenticated user's ID for ownership verification.
            resume_id: ID of the stored resume to render.
            template_id: Template to use (classic, modern, minimal).
            accent_color: Optional hex colour override for the template.

        Returns:
            Raw PDF bytes.

        Raises:
            ValidationError: If the template_id is not recognised.
            NotFoundError: If the resume does not exist or is not owned by the user.
        """
        # 1. Get template
        template = TemplateRegistry.get_template(template_id)
        if template is None:
            raise ValidationError(f"Unknown template: {template_id}")

        # 2. Load resume (verify ownership)
        stmt = select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        result = await session.execute(stmt)
        resume = result.scalar_one_or_none()
        if resume is None:
            raise NotFoundError("Resume not found")

        # 3. Load user + profile for contact info fallback
        user_stmt = select(User).where(User.id == user_id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await session.execute(profile_stmt)
        profile = profile_result.scalar_one_or_none()

        # 4. Build ResumeData from parsed_data + profile fallbacks
        parsed: dict[str, object] = resume.parsed_data or {}

        # Extract skills as list[str] from parsed or profile
        raw_skills = parsed.get("skills") or (profile.skills if profile else []) or []
        skills: list[str] = []
        for s in raw_skills:  # type: ignore[union-attr]
            if isinstance(s, str):
                skills.append(s)
            elif isinstance(s, dict):
                # Profile stores skills as [{"name": "Python", "level": "Advanced"}]
                name = s.get("name") or s.get("skill") or ""
                if name:
                    skills.append(str(name))

        # Extract languages as list[str]
        raw_languages = parsed.get("languages") or (profile.languages if profile else []) or []
        languages: list[str] = []
        for lang in raw_languages:  # type: ignore[union-attr]
            if isinstance(lang, str):
                languages.append(lang)
            elif isinstance(lang, dict):
                name = lang.get("name") or lang.get("language") or ""
                if name:
                    languages.append(str(name))

        # Experience and education as list[dict]
        experience_raw = parsed.get("experience") or []
        experience: list[dict[str, str | None]] = []
        for e in experience_raw:  # type: ignore[union-attr]
            if isinstance(e, dict):
                experience.append(e)  # type: ignore[arg-type]

        education_raw = parsed.get("education") or []
        education: list[dict[str, str | None]] = []
        for e in education_raw:  # type: ignore[union-attr]
            if isinstance(e, dict):
                education.append(e)  # type: ignore[arg-type]

        # Certifications
        raw_certs = parsed.get("certifications") or (
            profile.certifications if profile else []
        ) or []
        certifications: list[str] = [str(c) for c in raw_certs]  # type: ignore[union-attr]

        # Name fallback: parsed -> user
        full_name = str(parsed.get("full_name") or (user.full_name if user else "") or "")

        data = ResumeData(
            full_name=full_name,
            email=str(parsed.get("email") or "") or None,
            phone=getattr(profile, "phone", None) if profile else None,
            location=getattr(profile, "location", None) if profile else None,
            linkedin_url=getattr(profile, "linkedin_url", None) if profile else None,
            github_url=getattr(profile, "github_url", None) if profile else None,
            portfolio_url=getattr(profile, "portfolio_url", None) if profile else None,
            summary=str(parsed.get("summary") or "") or (
                getattr(profile, "summary", None) if profile else None
            ),
            skills=skills,
            experience=experience,
            education=education,
            certifications=certifications,
            languages=languages,
        )

        # 5. Render PDF
        pdf_bytes = template.render(data, accent_color=accent_color)
        log.info(
            "resume_pdf_generated",
            resume_id=str(resume_id),
            template=template_id,
            size=len(pdf_bytes),
        )
        return pdf_bytes
