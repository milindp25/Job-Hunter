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


@dataclass
class GeminiAtsResult:
    """Parsed result from Gemini ATS compliance analysis."""

    keyword_score: int = 0
    content_score: int = 0
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    keyword_findings: list[dict[str, object]] = field(default_factory=list)
    content_findings: list[dict[str, object]] = field(default_factory=list)
    suggestions: list[dict[str, str]] = field(default_factory=list)
    summary: str = ""


def is_gemini_configured() -> bool:
    """Check if the Gemini API key is configured."""
    settings = get_settings()
    return bool(settings.GEMINI_API_KEY)


async def _call_gemini_with_retry(
    model: object,
    prompt: str,
    max_retries: int = 3,
) -> object:
    """Call the Gemini SDK with exponential backoff retry on rate limit errors."""
    import asyncio

    import google.generativeai as genai

    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                model.generate_content,  # type: ignore[union-attr]
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            return response
        except Exception as exc:
            exc_str = str(exc).lower()
            is_rate_limit = "429" in exc_str or "rate" in exc_str
            if is_rate_limit and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                log.warning(
                    "gemini_rate_limit_retry",
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    error=str(exc),
                )
                await asyncio.sleep(wait)
                last_exc = exc
                continue
            last_exc = exc
            break

    raise GeminiAnalysisError(
        detail=f"Gemini call failed after {max_retries} retries: {last_exc}"
    ) from last_exc


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
        response = await _call_gemini_with_retry(model, prompt)

        result = _parse_gemini_response(response.text)  # type: ignore[union-attr]
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


async def analyze_ats(
    resume_text: str,
    parsed_data: dict[str, object],
    job_title: str,
    job_company: str,
    job_description: str,
    job_tags: list[str],
    format_findings_summary: str,
) -> GeminiAtsResult:
    """Send resume + job data to Gemini 2.0 Flash for ATS compliance analysis."""
    import google.generativeai as genai

    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise GeminiAnalysisError(detail="Gemini API key is not configured")

    genai.configure(api_key=settings.GEMINI_API_KEY)

    prompt = _build_ats_prompt(
        resume_text=resume_text,
        parsed_data=parsed_data,
        job_title=job_title,
        job_company=job_company,
        job_description=job_description,
        job_tags=job_tags,
        format_findings_summary=format_findings_summary,
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = await _call_gemini_with_retry(model, prompt)

        result = _parse_ats_response(response.text)  # type: ignore[union-attr]
        log.info(
            "gemini_ats_analysis_complete",
            job_title=job_title,
            keyword_score=result.keyword_score,
            content_score=result.content_score,
        )
        return result

    except GeminiAnalysisError:
        raise
    except Exception as exc:
        log.exception("gemini_ats_analysis_failed", job_title=job_title, error=str(exc))
        raise GeminiAnalysisError(detail=f"Gemini ATS analysis failed: {exc}") from None


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


def _build_ats_prompt(
    resume_text: str,
    parsed_data: dict[str, object],
    job_title: str,
    job_company: str,
    job_description: str,
    job_tags: list[str],
    format_findings_summary: str,
) -> str:
    """Build the structured prompt for Gemini ATS compliance analysis."""
    job_tags_str = ", ".join(job_tags) if job_tags else "Not specified"
    resume_snippet = resume_text[:4000] if resume_text else "No resume text available"

    skills = parsed_data.get("skills", [])
    skills_str = ", ".join(str(s) for s in skills) if skills else "Not extracted"  # type: ignore[union-attr]

    return f"""You are an expert ATS (Applicant Tracking System) compliance analyst. \
Analyze this resume against the job posting for keyword and content quality.

## RESUME TEXT (first 4000 chars)
{resume_snippet}

## PARSED RESUME DATA
- Skills detected: {skills_str}

## JOB POSTING
**Title:** {job_title}
**Company:** {job_company}
**Required Skills/Tags:** {job_tags_str}

**Description:**
{job_description[:3000]}

## FORMAT FINDINGS (already caught — do NOT repeat these)
{format_findings_summary or "None"}

## ANALYSIS RULES
- Keyword scoring: start at 100, deduct 5 points per missing important keyword (min 0)
- Flag vague language: "responsible for", "helped with", "worked on", "assisted with"
- Suggest spelling out acronyms on first use if not already done
- Provide at most 3 improvement suggestions with concrete before/after rewrites
- Do NOT repeat any format findings listed above

## INSTRUCTIONS

Return a JSON object with this exact structure:

{{
  "keyword_analysis": {{
    "score": <0-100 integer>,
    "matched_keywords": ["keyword1", "keyword2"],
    "missing_keywords": ["keyword3", "keyword4"],
    "findings": [
      {{
        "rule_id": "missing_keyword",
        "severity": "warning",
        "title": "Missing keyword: <name>",
        "detail": "Job mentions <name> N times but it does not appear in the resume.",
        "suggestion": "Add <name> to the skills section or relevant experience bullet.",
        "section": "skills",
        "metadata": {{"keyword": "<name>", "job_mentions": 3}}
      }}
    ]
  }},
  "content_analysis": {{
    "score": <0-100 integer>,
    "findings": [
      {{
        "rule_id": "vague_language",
        "severity": "warning",
        "title": "Generic phrasing detected",
        "detail": "'Responsible for managing team of 5...'",
        "suggestion": "Use action verbs with quantified results, e.g. 'Led a 5-person team...'",
        "section": "experience",
        "metadata": {{"original_text": "Responsible for managing team of 5"}}
      }}
    ]
  }},
  "suggestions": [
    {{
      "section": "experience",
      "before": "Original resume text",
      "after": "Improved resume text with action verb and metrics",
      "reason": "Why this change improves ATS compatibility and recruiter appeal",
      "estimated_impact": "+15 pts"
    }}
  ],
  "summary": "2-3 sentence overall summary of ATS compliance and top priorities."
}}

Be specific and actionable. Base findings on actual evidence from the resume and job description."""


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


def _parse_ats_response(response_text: str) -> GeminiAtsResult:
    """Parse JSON response from Gemini into a GeminiAtsResult."""
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        log.warning("gemini_ats_response_not_json", response_text=response_text[:200])
        return GeminiAtsResult()

    def _clamp_score(value: object) -> int:
        """Clamp a value to 0-100 integer."""
        try:
            score = int(value)  # type: ignore[arg-type]
            return max(0, min(100, score))
        except (ValueError, TypeError):
            return 0

    keyword_analysis = data.get("keyword_analysis", {})
    content_analysis = data.get("content_analysis", {})
    raw_suggestions: list[object] = list(data.get("suggestions", []))

    # Coerce each suggestion to dict[str, str], limit to 3
    suggestions: list[dict[str, str]] = []
    for item in raw_suggestions[:3]:
        if isinstance(item, dict):
            suggestions.append({str(k): str(v) for k, v in item.items()})

    return GeminiAtsResult(
        keyword_score=_clamp_score(keyword_analysis.get("score", 0)),
        content_score=_clamp_score(content_analysis.get("score", 0)),
        matched_keywords=list(keyword_analysis.get("matched_keywords", [])),
        missing_keywords=list(keyword_analysis.get("missing_keywords", [])),
        keyword_findings=list(keyword_analysis.get("findings", [])),
        content_findings=list(content_analysis.get("findings", [])),
        suggestions=suggestions,
        summary=str(data.get("summary", "")),
    )
