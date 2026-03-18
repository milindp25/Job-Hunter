from __future__ import annotations

import uuid

from app.models.user import UserProfile
from app.services.user import calculate_profile_completeness


class TestProfileCompleteness:
    """Tests for the profile completeness calculator."""

    def _make_profile(self, **kwargs: object) -> UserProfile:
        """Create a UserProfile with sensible defaults, overriding with kwargs."""
        defaults: dict[str, object] = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "phone": None,
            "location": None,
            "linkedin_url": None,
            "github_url": None,
            "portfolio_url": None,
            "years_of_experience": None,
            "desired_roles": [],
            "desired_locations": [],
            "min_salary": None,
            "skills": [],
            "education": [],
            "experience": [],
            "certifications": [],
            "languages": [],
            "summary": None,
            "onboarding_completed": False,
            "profile_completeness": 0,
        }
        defaults.update(kwargs)
        return UserProfile(**defaults)  # type: ignore[arg-type]

    async def test_empty_profile_is_zero(self) -> None:
        profile = self._make_profile()
        score = await calculate_profile_completeness(profile)
        assert score == 0

    async def test_full_profile_is_100(self) -> None:
        profile = self._make_profile(
            phone="+1234567890",
            location="San Francisco, CA",
            summary="Senior full-stack engineer with 10 years of experience.",
            linkedin_url="https://linkedin.com/in/testuser",
            skills=[
                {"name": "Python", "level": "expert", "years": 5},
                {"name": "TypeScript", "level": "advanced", "years": 3},
                {"name": "Go", "level": "intermediate", "years": 2},
            ],
            experience=[
                {
                    "company": "Acme",
                    "title": "Senior Dev",
                    "description": "Built things",
                    "start_date": "2020-01",
                }
            ],
            education=[
                {
                    "institution": "MIT",
                    "degree": "B.S.",
                    "field": "CS",
                    "start_date": "2014-09",
                }
            ],
            desired_roles=["Backend Engineer"],
            desired_locations=["Remote"],
            min_salary=150000,
            certifications=["AWS Solutions Architect"],
        )
        score = await calculate_profile_completeness(profile)
        assert score == 100

    async def test_partial_profile_phone_and_location(self) -> None:
        """phone (+5) + location (+5) = 10."""
        profile = self._make_profile(
            phone="+1234567890",
            location="NYC",
        )
        score = await calculate_profile_completeness(profile)
        assert score == 10

    async def test_partial_profile_skills_under_three(self) -> None:
        """1-2 skills earn +15, but not the bonus +10 for >= 3 skills."""
        profile = self._make_profile(
            skills=[{"name": "Python", "level": "advanced", "years": 3}],
        )
        score = await calculate_profile_completeness(profile)
        assert score == 15

    async def test_partial_profile_skills_three_or_more(self) -> None:
        """3+ skills earn +15 + +10 = 25."""
        profile = self._make_profile(
            skills=[
                {"name": "Python", "level": "expert", "years": 5},
                {"name": "TypeScript", "level": "advanced", "years": 3},
                {"name": "Go", "level": "intermediate", "years": 1},
            ],
        )
        score = await calculate_profile_completeness(profile)
        assert score == 25

    async def test_partial_profile_summary_only(self) -> None:
        """summary = +10."""
        profile = self._make_profile(summary="A great developer.")
        score = await calculate_profile_completeness(profile)
        assert score == 10

    async def test_partial_profile_experience_and_education(self) -> None:
        """experience (+15) + education (+10) = 25."""
        profile = self._make_profile(
            experience=[{"company": "Acme", "title": "Dev", "description": "Work", "start_date": "2020"}],
            education=[{"institution": "MIT", "degree": "BS", "field": "CS", "start_date": "2014"}],
        )
        score = await calculate_profile_completeness(profile)
        assert score == 25

    async def test_partial_profile_desired_roles_and_locations(self) -> None:
        """desired_roles (+10) + desired_locations (+5) = 15."""
        profile = self._make_profile(
            desired_roles=["Backend"],
            desired_locations=["Remote"],
        )
        score = await calculate_profile_completeness(profile)
        assert score == 15

    async def test_partial_profile_salary_and_certs(self) -> None:
        """min_salary (+5) + certifications (+5) = 10."""
        profile = self._make_profile(
            min_salary=100000,
            certifications=["AWS"],
        )
        score = await calculate_profile_completeness(profile)
        assert score == 10
