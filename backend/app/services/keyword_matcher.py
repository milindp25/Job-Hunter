from __future__ import annotations

import re
from dataclasses import dataclass

import structlog

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

_EXPERIENCE_RE = re.compile(r"(\d+)\+?\s*years?", re.IGNORECASE)

# Skill level weights for scoring — experts contribute more than beginners.
_LEVEL_WEIGHTS: dict[str, int] = {
    "expert": 4,
    "advanced": 3,
    "intermediate": 2,
    "beginner": 1,
}

# Overall score category weights (must sum to 1.0).
_CATEGORY_WEIGHTS: dict[str, float] = {
    "skills": 0.35,
    "role": 0.25,
    "location": 0.15,
    "salary": 0.15,
    "experience": 0.10,
}


@dataclass
class KeywordMatchResult:
    """Result of Layer 1 keyword matching."""

    overall_score: int = 0  # weighted average, 0-100
    skills_score: int = 0  # 0-100
    role_score: int = 0  # 0-100
    location_score: int = 0  # 0-100
    salary_score: int = 0  # 0-100
    experience_score: int = 0  # 0-100


# ---------------------------------------------------------------------------
# Tokenizer helper
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    """Lowercase *text*, split on non-alphanumeric chars, and drop empties."""
    return {tok for tok in re.split(r"[^a-zA-Z0-9]+", text.lower()) if tok}


# ---------------------------------------------------------------------------
# Individual score calculators
# ---------------------------------------------------------------------------


def _calculate_skills_score(
    user_skills: list[dict[str, str | float]],
    job_tags: list[str],
    job_description: str,
) -> int:
    """Score how well user skills match the job tags and description.

    Each skill is weighted by proficiency level (expert > beginner).
    Matching is case-insensitive: exact match against tags or word-boundary
    match inside the description.
    """
    if not user_skills:
        return 0

    lower_tags: set[str] = {t.lower() for t in job_tags}
    lower_desc: str = job_description.lower()

    total_weight: float = 0.0
    matched_weight: float = 0.0

    for skill in user_skills:
        name_raw = skill.get("name", "")
        if not isinstance(name_raw, str) or not name_raw.strip():
            continue

        name = name_raw.strip().lower()
        level_raw = skill.get("level", "intermediate")
        level = str(level_raw).strip().lower() if level_raw else "intermediate"
        weight = _LEVEL_WEIGHTS.get(level, 2)

        total_weight += weight

        # 1) Exact match in tags
        if name in lower_tags:
            matched_weight += weight
            continue

        # 2) Word-boundary match in description
        pattern = re.compile(rf"\b{re.escape(name)}\b")
        if pattern.search(lower_desc):
            matched_weight += weight

    if total_weight == 0:
        return 0

    return min(100, round((matched_weight / total_weight) * 100))


def _calculate_role_score(
    user_desired_roles: list[str],
    job_title: str,
) -> int:
    """Score how well the job title matches the user's desired roles.

    If any desired role is fully contained in the title we return 100.
    Otherwise we compute Jaccard word-overlap and return the best score.
    """
    if not user_desired_roles:
        return 50  # neutral when no preferences expressed

    lower_title = job_title.lower().strip()
    if not lower_title:
        return 50

    title_tokens = _tokenize(lower_title)
    best_score = 0

    for role in user_desired_roles:
        lower_role = role.lower().strip()
        if not lower_role:
            continue

        # Exact containment
        if lower_role in lower_title:
            return 100

        # Jaccard similarity on word tokens
        role_tokens = _tokenize(lower_role)
        if not role_tokens or not title_tokens:
            continue

        intersection = role_tokens & title_tokens
        union = role_tokens | title_tokens
        jaccard = len(intersection) / len(union) if union else 0.0
        score = round(jaccard * 100)
        best_score = max(best_score, score)

    return best_score


def _calculate_location_score(
    user_desired_locations: list[str],
    job_location: str | None,
    job_is_remote: bool,
) -> int:
    """Score location compatibility between user preferences and job.

    Remote jobs are always highly rated; exact location substring matches
    score 100.
    """
    lower_prefs = [loc.lower().strip() for loc in user_desired_locations if loc.strip()]

    # Check if user explicitly desires remote
    user_wants_remote = any("remote" in pref for pref in lower_prefs)

    if user_wants_remote and job_is_remote:
        return 100

    if job_is_remote:
        return 80

    lower_job_loc = job_location.lower().strip() if job_location else ""

    # Both sides have location info — try substring match
    if lower_job_loc and lower_prefs:
        for pref in lower_prefs:
            if pref in lower_job_loc or lower_job_loc in pref:
                return 100

    # No info on either side — neutral
    if not lower_job_loc and not lower_prefs:
        return 50

    # One side missing — slight neutral
    if not lower_job_loc or not lower_prefs:
        return 50

    # Both have info, but no overlap
    return 20


def _calculate_salary_score(
    user_min_salary: int | None,
    job_salary_min: int | None,
    job_salary_max: int | None,
) -> int:
    """Score salary compatibility.

    The best relevant salary figure from the job is compared against the
    user's minimum expectation with a two-tier fallback.
    """
    job_has_salary = job_salary_min is not None or job_salary_max is not None

    if user_min_salary is None and not job_has_salary:
        return 50  # neutral — no data on either side

    if user_min_salary is None and job_has_salary:
        return 50  # user has no preference

    if user_min_salary is not None and not job_has_salary:
        return 50  # can't evaluate

    # Both sides have data — compare job's best offer against user minimum.
    best_offer = job_salary_max if job_salary_max is not None else job_salary_min
    assert best_offer is not None  # guaranteed by the checks above
    assert user_min_salary is not None

    if best_offer >= user_min_salary:
        return 100

    threshold_80 = int(user_min_salary * 0.8)
    if best_offer >= threshold_80:
        return 60

    return 20


def _calculate_experience_score(
    user_years: int | None,
    job_description: str,
) -> int:
    """Score experience-level fit by extracting year requirements from text.

    Uses a regex to pull numbers like "3+ years" or "5 years" from the job
    description and compares against the user's declared experience.
    """
    matches = _EXPERIENCE_RE.findall(job_description)
    if not matches or user_years is None:
        return 50  # neutral — no data

    required_years = max(int(m) for m in matches)

    if user_years >= required_years:
        return 100

    if user_years >= required_years - 2:
        return 60

    return 20


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_keyword_match(
    *,
    user_skills: list[dict[str, str | float]],
    user_desired_roles: list[str],
    user_desired_locations: list[str],
    user_min_salary: int | None,
    user_years_of_experience: int | None,
    job_title: str,
    job_description: str,
    job_tags: list[str],
    job_location: str | None,
    job_is_remote: bool,
    job_salary_min: int | None,
    job_salary_max: int | None,
) -> KeywordMatchResult:
    """Layer 1 keyword matcher — fast, deterministic, no LLM calls.

    Computes individual sub-scores for skills, role, location, salary, and
    experience, then produces a weighted overall score.

    All parameters are keyword-only to prevent accidental mis-ordering.
    """
    skills = _calculate_skills_score(user_skills, job_tags, job_description)
    role = _calculate_role_score(user_desired_roles, job_title)
    location = _calculate_location_score(
        user_desired_locations, job_location, job_is_remote
    )
    salary = _calculate_salary_score(user_min_salary, job_salary_min, job_salary_max)
    experience = _calculate_experience_score(user_years_of_experience, job_description)

    overall = round(
        skills * _CATEGORY_WEIGHTS["skills"]
        + role * _CATEGORY_WEIGHTS["role"]
        + location * _CATEGORY_WEIGHTS["location"]
        + salary * _CATEGORY_WEIGHTS["salary"]
        + experience * _CATEGORY_WEIGHTS["experience"]
    )

    result = KeywordMatchResult(
        overall_score=overall,
        skills_score=skills,
        role_score=role,
        location_score=location,
        salary_score=salary,
        experience_score=experience,
    )

    log.debug(
        "keyword_match_calculated",
        overall=overall,
        skills=skills,
        role=role,
        location=location,
        salary=salary,
        experience=experience,
        job_title=job_title,
    )

    return result
