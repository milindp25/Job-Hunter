from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

import structlog
from sqlmodel import select

from app.exceptions import NotFoundError
from app.models.job import Job
from app.models.resume import Resume
from app.models.tailored_resume import TailoredResume
from app.services.gemini import generate_json

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

_TAILOR_PROMPT_V1 = """\
You are an expert resume consultant. Your task is to tailor a resume to better \
match a specific job description. You must NEVER fabricate or invent experience, \
skills, or qualifications that the candidate does not already have. You may only \
reword, reorganize, and emphasize existing experience to better align with the job.

## Original Resume Data

### Summary
{summary}

### Experience
{experience}

### Skills
{skills}

## Job Description

**Title:** {job_title}
**Company:** {job_company}

{job_description}

## Instructions

Analyze the resume against the job description and return a JSON object with \
exactly these keys:

1. "tailored_summary" (string): A rewritten professional summary that emphasizes \
skills and experience most relevant to this job. Keep the same facts but adjust \
emphasis and wording.

2. "tailored_experience" (array of objects): Each object should have:
   - "title" (string): job title (keep original)
   - "company" (string): company name (keep original)
   - "duration" (string): time period (keep original)
   - "highlights" (array of strings): bullet points rewritten to emphasize \
keywords and skills from the job description. Do NOT add accomplishments the \
candidate did not have. Only rephrase existing bullets.

3. "tailored_skills" (array of strings): The candidate's skills reordered so the \
most relevant skills for this job appear first. You may add skills ONLY if the \
candidate's experience clearly demonstrates them (e.g., if they used Python in \
a project, you can list Python).

4. "keyword_matches" (array of strings): Keywords from the job description that \
are already present in the original resume.

5. "keyword_gaps" (array of strings): Important keywords from the job description \
that are NOT present in the original resume and the candidate should consider \
adding if truthful.

6. "match_score_before" (integer 0-100): Estimated match percentage of the \
original resume against this job.

7. "match_score_after" (integer 0-100): Estimated match percentage after tailoring.

Return ONLY valid JSON. No markdown, no explanation.
"""


class ResumeTailorService:
    """Service for tailoring resumes to specific job descriptions using AI."""

    async def tailor_resume(
        self,
        session: AsyncSession,
        user_id: str,
        resume_id: str,
        job_id: str,
    ) -> TailoredResume:
        """Tailor a resume to match a specific job description using Gemini AI.

        Non-destructive: creates a new TailoredResume record, never modifies
        the original Resume.

        Args:
            session: Database session.
            user_id: Authenticated user ID.
            resume_id: ID of the resume to tailor.
            job_id: ID of the target job.

        Returns:
            Created TailoredResume record.

        Raises:
            NotFoundError: If resume or job not found, or resume doesn't belong to user.
        """
        user_uuid = uuid.UUID(user_id)
        resume_uuid = uuid.UUID(resume_id)
        job_uuid = uuid.UUID(job_id)

        # Load resume and verify ownership
        stmt = select(Resume).where(Resume.id == resume_uuid, Resume.user_id == user_uuid)
        result = await session.exec(stmt)
        resume = result.first()
        if resume is None:
            log.warning("tailor_resume_not_found", resume_id=resume_id, user_id=user_id)
            raise NotFoundError(detail="Resume not found")

        # Load job
        stmt_job = select(Job).where(Job.id == job_uuid)
        result_job = await session.exec(stmt_job)
        job = result_job.first()
        if job is None:
            log.warning("tailor_job_not_found", job_id=job_id)
            raise NotFoundError(detail="Job not found")

        # Extract resume sections from parsed_data
        parsed = resume.parsed_data or {}
        summary = parsed.get("summary", "") or ""
        experience = parsed.get("experience", [])
        skills = parsed.get("skills", [])

        # Build prompt
        prompt = _TAILOR_PROMPT_V1.format(
            summary=summary or "(No summary provided)",
            experience=json.dumps(experience, indent=2) if experience else "(No experience data)",
            skills=", ".join(skills) if isinstance(skills, list) else str(skills),
            job_title=job.title,
            job_company=job.company,
            job_description=job.description or "(No description available)",
        )

        log.info(
            "tailor_request_started",
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
        )

        # Call Gemini
        ai_result = await generate_json(prompt, schema_hint="resume_tailor_v1")

        # Parse response
        tailored_summary = str(ai_result.get("tailored_summary", ""))
        tailored_experience: list[dict[str, object]] = ai_result.get(
            "tailored_experience", []
        )  # type: ignore[assignment]
        tailored_skills: list[str] = ai_result.get(
            "tailored_skills", []
        )  # type: ignore[assignment]
        keyword_matches: list[str] = ai_result.get(
            "keyword_matches", []
        )  # type: ignore[assignment]
        keyword_gaps: list[str] = ai_result.get(
            "keyword_gaps", []
        )  # type: ignore[assignment]
        match_score_before = int(ai_result.get("match_score_before", 0) or 0)
        match_score_after = int(ai_result.get("match_score_after", 0) or 0)

        # Create record
        tailored = TailoredResume(
            user_id=user_uuid,
            resume_id=resume_uuid,
            job_id=job_uuid,
            tailored_summary=tailored_summary or None,
            tailored_experience=tailored_experience,
            tailored_skills=tailored_skills,
            keyword_matches=keyword_matches,
            keyword_gaps=keyword_gaps,
            match_score_before=match_score_before,
            match_score_after=match_score_after,
            ai_model="gemini-2.0-flash",
            prompt_version="v1",
        )
        session.add(tailored)
        await session.flush()

        log.info(
            "tailor_request_completed",
            tailored_id=tailored.id,
            user_id=user_id,
            score_before=match_score_before,
            score_after=match_score_after,
        )

        return tailored

    async def get_tailored_resume(
        self,
        session: AsyncSession,
        user_id: str,
        tailored_id: str,
    ) -> TailoredResume:
        """Get a specific tailored resume by ID, verifying ownership.

        Raises:
            NotFoundError: If not found or not owned by user.
        """
        user_uuid = uuid.UUID(user_id)
        tailored_uuid = uuid.UUID(tailored_id)
        stmt = select(TailoredResume).where(
            TailoredResume.id == tailored_uuid,
            TailoredResume.user_id == user_uuid,
        )
        result = await session.exec(stmt)
        tailored = result.first()
        if tailored is None:
            raise NotFoundError(detail="Tailored resume not found")
        return tailored

    async def list_tailored_resumes(
        self,
        session: AsyncSession,
        user_id: str,
        resume_id: str | None = None,
        job_id: str | None = None,
    ) -> list[TailoredResume]:
        """List tailored resumes for a user with optional filters."""
        user_uuid = uuid.UUID(user_id)
        stmt = select(TailoredResume).where(TailoredResume.user_id == user_uuid)

        if resume_id is not None:
            stmt = stmt.where(TailoredResume.resume_id == uuid.UUID(resume_id))
        if job_id is not None:
            stmt = stmt.where(TailoredResume.job_id == uuid.UUID(job_id))

        stmt = stmt.order_by(TailoredResume.created_at.desc())  # type: ignore[union-attr]
        result = await session.exec(stmt)
        return list(result.all())

    async def delete_tailored_resume(
        self,
        session: AsyncSession,
        user_id: str,
        tailored_id: str,
    ) -> None:
        """Delete a tailored resume, verifying ownership.

        Raises:
            NotFoundError: If not found or not owned by user.
        """
        tailored = await self.get_tailored_resume(session, user_id, tailored_id)
        await session.delete(tailored)
        await session.flush()

        log.info("tailored_resume_deleted", tailored_id=tailored_id, user_id=user_id)
