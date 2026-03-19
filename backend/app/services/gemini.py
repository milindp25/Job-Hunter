from __future__ import annotations

import json
from dataclasses import dataclass, field

import structlog

from app.config import get_settings
from app.exceptions import GeminiAnalysisError

log = structlog.get_logger()


@dataclass
class GeminiMatchResult:
    """Parsed result from Gemini job matching analysis."""

    overall_score: int = 0
    skills_match: int = 0
    experience_match: int = 0
    education_match: int = 0
    location_match: int = 0
    salary_match: int = 0
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    recommendation: str = "Moderate Match"


def is_gemini_configured() -> bool:
    """Check if the Gemini API key is configured."""
    settings = get_settings()
    return bool(settings.GEMINI_API_KEY)


async def analyze_job_match(
    profile_summary: str,
    resume_text: str,
    job_title: str,
    job_company: str,
    job_description: str,
    job_tags: list[str],
    job_location: str | None,
    job_is_remote: bool,
    job_salary_min: int | None,
    job_salary_max: int | None,
    user_desired_roles: list[str],
    user_desired_locations: list[str],
    user_min_salary: int | None,
    user_years_of_experience: int | None,
) -> GeminiMatchResult:
    """Send profile + resume + job data to Gemini 2.0 Flash for structured match analysis."""
    import asyncio

    import google.generativeai as genai

    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise GeminiAnalysisError(detail="Gemini API key is not configured")

    genai.configure(api_key=settings.GEMINI_API_KEY)

    prompt = _build_match_prompt(
        profile_summary=profile_summary,
        resume_text=resume_text,
        job_title=job_title,
        job_company=job_company,
        job_description=job_description,
        job_tags=job_tags,
        job_location=job_location,
        job_is_remote=job_is_remote,
        job_salary_min=job_salary_min,
        job_salary_max=job_salary_max,
        user_desired_roles=user_desired_roles,
        user_desired_locations=user_desired_locations,
        user_min_salary=user_min_salary,
        user_years_of_experience=user_years_of_experience,
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Run the synchronous SDK call in a thread to not block async
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,  # Low temperature for consistent scoring
            ),
        )

        result = _parse_gemini_response(response.text)
        log.info(
            "gemini_analysis_complete",
            job_title=job_title,
            overall_score=result.overall_score,
            recommendation=result.recommendation,
        )
        return result

    except GeminiAnalysisError:
        raise
    except Exception as exc:
        log.exception("gemini_analysis_failed", job_title=job_title, error=str(exc))
        raise GeminiAnalysisError(detail=f"Gemini analysis failed: {exc}") from None


def _build_match_prompt(
    profile_summary: str,
    resume_text: str,
    job_title: str,
    job_company: str,
    job_description: str,
    job_tags: list[str],
    job_location: str | None,
    job_is_remote: bool,
    job_salary_min: int | None,
    job_salary_max: int | None,
    user_desired_roles: list[str],
    user_desired_locations: list[str],
    user_min_salary: int | None,
    user_years_of_experience: int | None,
) -> str:
    """Build the structured prompt for Gemini job matching analysis."""
    desired_roles = ", ".join(user_desired_roles) if user_desired_roles else "Not specified"
    desired_locs = ", ".join(user_desired_locations) if user_desired_locations else "Not specified"
    job_tags_str = ", ".join(job_tags) if job_tags else "Not specified"

    salary_info = "Not specified"
    if job_salary_min and job_salary_max:
        salary_info = f"${job_salary_min:,} - ${job_salary_max:,}"
    elif job_salary_min:
        salary_info = f"From ${job_salary_min:,}"
    elif job_salary_max:
        salary_info = f"Up to ${job_salary_max:,}"

    user_salary_info = f"${user_min_salary:,}" if user_min_salary else "Not specified"

    return f"""You are an expert job matching analyst. Analyze how well this candidate matches \
this job posting.

## CANDIDATE PROFILE

**Professional Summary:**
{profile_summary or "Not provided"}

**Resume:**
{resume_text[:3000] if resume_text else "No resume uploaded"}

**Preferences:**
- Desired Roles: {desired_roles}
- Desired Locations: {desired_locs}
- Minimum Salary: {user_salary_info}
- Years of Experience: {user_years_of_experience or "Not specified"}

## JOB POSTING

**Title:** {job_title}
**Company:** {job_company}
**Location:** {job_location or "Not specified"} {"(Remote)" if job_is_remote else ""}
**Salary Range:** {salary_info}
**Required Skills/Tags:** {job_tags_str}

**Description:**
{job_description[:3000]}

## INSTRUCTIONS

Analyze the match between this candidate and job posting. Return a JSON object with these \
exact fields:

1. "overall_score": 0-100 (how well the candidate matches overall)
2. "skills_match": 0-100 (how well candidate's skills match job requirements)
3. "experience_match": 0-100 (how well candidate's experience level and type matches)
4. "education_match": 0-100 (how well education background aligns)
5. "location_match": 0-100 (location/remote compatibility)
6. "salary_match": 0-100 (salary expectations vs offering)
7. "strengths": list of 2-4 specific reasons this is a good match
8. "gaps": list of 1-3 specific qualifications the candidate may lack
9. "recommendation": exactly one of "Strong Match", "Good Match", "Moderate Match", "Weak Match"

Be realistic and specific in your analysis. Base scores on actual evidence from the resume \
and job description."""


def _parse_gemini_response(response_text: str) -> GeminiMatchResult:
    """Parse JSON response from Gemini into a GeminiMatchResult."""
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        log.warning("gemini_response_not_json", response_text=response_text[:200])
        return GeminiMatchResult()  # Return defaults on parse failure

    def _clamp_score(value: object) -> int:
        """Clamp a value to 0-100 integer."""
        try:
            score = int(value)  # type: ignore[arg-type]
            return max(0, min(100, score))
        except (ValueError, TypeError):
            return 0

    return GeminiMatchResult(
        overall_score=_clamp_score(data.get("overall_score", 0)),
        skills_match=_clamp_score(data.get("skills_match", 0)),
        experience_match=_clamp_score(data.get("experience_match", 0)),
        education_match=_clamp_score(data.get("education_match", 0)),
        location_match=_clamp_score(data.get("location_match", 0)),
        salary_match=_clamp_score(data.get("salary_match", 0)),
        strengths=list(data.get("strengths", [])),
        gaps=list(data.get("gaps", [])),
        recommendation=str(data.get("recommendation", "Moderate Match")),
    )
