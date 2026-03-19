from __future__ import annotations

import types
import uuid
from datetime import UTC, datetime

from app.services.ats_rules import (
    calculate_format_score,
    check_bullet_characters,
    check_contact_info,
    check_file_size,
    check_parseable_text,
    check_resume_length,
    check_standard_sections,
    check_text_quality,
    run_all_rules,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_SAMPLE_RAW_TEXT = (
    "John Doe\n"
    "john.doe@example.com\n"
    "555-123-4567\n"
    "San Francisco, CA\n"
    "\n"
    "Experience\n"
    "Senior Software Engineer at Acme Corp, Jan 2020 - Dec 2023\n"
    "- Built microservices using Python and FastAPI handling one million requests per day\n"
    "- Deployed applications on AWS using ECS Fargate with automated CI/CD pipelines\n"
    "- Led a team of four engineers delivering three major product features on schedule\n"
    "- Reduced API latency by forty percent through query optimisation and Redis caching\n"
    "\n"
    "Software Engineer at StartupXYZ, Mar 2017 - Dec 2019\n"
    "- Developed a customer dashboard using React and TypeScript for fifty thousand users\n"
    "- Integrated Stripe and PayPal payment gateways processing ten thousand daily orders\n"
    "- Collaborated with product and design teams to refine user stories and criteria\n"
    "\n"
    "Education\n"
    "B.S. Computer Science, State University, 2013 - 2017\n"
    "GPA 3.8 out of 4.0, Dean's List three semesters\n"
    "\n"
    "Skills\n"
    "Python, TypeScript, React, PostgreSQL, Redis, Docker, AWS, FastAPI, SQLAlchemy, Git"
)


def _make_resume(
    raw_text: str = _SAMPLE_RAW_TEXT,
    file_size: int = 50_000,
    file_type: str = "pdf",
    parsed_data: dict | None = None,
    resume_id: uuid.UUID | None = None,
    updated_at: datetime | None = None,
) -> types.SimpleNamespace:
    """Return a mock resume object with the expected attributes."""
    if parsed_data is None:
        parsed_data = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "skills": ["Python", "TypeScript", "React"],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Acme Corp",
                    "start_date": "2020",
                    "end_date": "2023",
                }
            ],
        }
    return types.SimpleNamespace(
        id=resume_id or uuid.uuid4(),
        raw_text=raw_text,
        file_size=file_size,
        file_type=file_type,
        parsed_data=parsed_data,
        updated_at=updated_at or datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# TestParseableText
# ---------------------------------------------------------------------------


class TestParseableText:
    def test_normal_resume_passes(self) -> None:
        resume = _make_resume()
        result = check_parseable_text(resume)
        assert result is None

    def test_empty_text_is_blocker(self) -> None:
        resume = _make_resume(raw_text="", file_size=50_000)
        result = check_parseable_text(resume)
        assert result is not None
        assert result["severity"] == "blocker"

    def test_very_short_text_with_large_file_is_blocker(self) -> None:
        # 30 chars of text but 50 KB file — looks like garbled/image PDF
        resume = _make_resume(raw_text="hi" * 15, file_size=50_000)
        result = check_parseable_text(resume)
        assert result is not None
        assert result["severity"] == "blocker"

    def test_short_text_small_file_passes(self) -> None:
        # tiny file and tiny text — genuinely small, not scanned
        resume = _make_resume(raw_text="hi" * 15, file_size=5_000)
        result = check_parseable_text(resume)
        assert result is None


# ---------------------------------------------------------------------------
# TestTextQuality
# ---------------------------------------------------------------------------


class TestTextQuality:
    def test_clean_text_passes(self) -> None:
        resume = _make_resume()
        result = check_text_quality(resume)
        assert result is None

    def test_garbled_text_is_critical(self) -> None:
        # >20% non-word characters
        garbled = "abc " * 30 + "##@!%%^^&&**" * 40
        resume = _make_resume(raw_text=garbled)
        result = check_text_quality(resume)
        assert result is not None
        assert result["severity"] == "critical"


# ---------------------------------------------------------------------------
# TestContactInfo
# ---------------------------------------------------------------------------


class TestContactInfo:
    def test_complete_contact_info_passes(self) -> None:
        resume = _make_resume()
        result = check_contact_info(resume)
        assert result is None

    def test_missing_email_is_warning(self) -> None:
        resume = _make_resume(
            parsed_data={
                "full_name": "John Doe",
                "email": None,
                "phone": "555-123-4567",
                "skills": [],
                "experience": [],
            }
        )
        result = check_contact_info(resume)
        assert result is not None
        assert result["severity"] == "warning"

    def test_missing_phone_is_warning(self) -> None:
        resume = _make_resume(
            parsed_data={
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": None,
                "skills": [],
                "experience": [],
            }
        )
        result = check_contact_info(resume)
        assert result is not None
        assert result["severity"] == "warning"

    def test_missing_name_is_warning(self) -> None:
        resume = _make_resume(
            parsed_data={
                "full_name": None,
                "email": "john@example.com",
                "phone": "555-123-4567",
                "skills": [],
                "experience": [],
            }
        )
        result = check_contact_info(resume)
        assert result is not None
        assert result["severity"] == "warning"


# ---------------------------------------------------------------------------
# TestStandardSections
# ---------------------------------------------------------------------------


class TestStandardSections:
    def test_standard_headers_present_passes(self) -> None:
        resume = _make_resume()
        result = check_standard_sections(resume)
        assert result is None

    def test_missing_experience_is_warning(self) -> None:
        no_experience = """
John Doe
john@example.com

Education
B.S. Computer Science, State University

Skills
Python, React
""".strip()
        resume = _make_resume(raw_text=no_experience)
        result = check_standard_sections(resume)
        assert result is not None
        assert result["severity"] == "warning"


# ---------------------------------------------------------------------------
# TestResumeLength
# ---------------------------------------------------------------------------


class TestResumeLength:
    def test_normal_length_passes(self) -> None:
        # ~200 words — well within normal range
        resume = _make_resume()
        result = check_resume_length(resume)
        assert result is None

    def test_too_short_is_warning(self) -> None:
        short_text = "John Doe Software Engineer Python React"  # <100 words
        resume = _make_resume(raw_text=short_text)
        result = check_resume_length(resume)
        assert result is not None
        assert result["severity"] == "warning"

    def test_too_long_is_warning(self) -> None:
        # Need >1500 words
        very_long = ("word " * 1600).strip()
        resume = _make_resume(raw_text=very_long)
        result = check_resume_length(resume)
        assert result is not None
        assert result["severity"] == "warning"


# ---------------------------------------------------------------------------
# TestBulletCharacters
# ---------------------------------------------------------------------------


class TestBulletCharacters:
    def test_standard_bullets_pass(self) -> None:
        text = _SAMPLE_RAW_TEXT + "\n- Standard bullet\n• Another bullet"
        resume = _make_resume(raw_text=text)
        result = check_bullet_characters(resume)
        assert result is None

    def test_fancy_bullets_are_warning(self) -> None:
        text = _SAMPLE_RAW_TEXT + "\n► Fancy bullet\n★ Star bullet\n➤ Arrow bullet"
        resume = _make_resume(raw_text=text)
        result = check_bullet_characters(resume)
        assert result is not None
        assert result["severity"] == "warning"


# ---------------------------------------------------------------------------
# TestFileSize
# ---------------------------------------------------------------------------


class TestFileSize:
    def test_normal_size_passes(self) -> None:
        resume = _make_resume(file_size=500_000)  # 500 KB
        result = check_file_size(resume)
        assert result is None

    def test_over_2mb_is_info(self) -> None:
        resume = _make_resume(file_size=3_000_000)  # 3 MB
        result = check_file_size(resume)
        assert result is not None
        assert result["severity"] == "info"


# ---------------------------------------------------------------------------
# TestFormatScore
# ---------------------------------------------------------------------------


class TestFormatScore:
    def test_perfect_score_no_findings(self) -> None:
        score, has_blocker, has_critical = calculate_format_score([])
        assert score == 100
        assert has_blocker is False
        assert has_critical is False

    def test_blocker_deduction(self) -> None:
        findings = [{"severity": "blocker"}]
        score, has_blocker, has_critical = calculate_format_score(findings)
        assert score == 30  # 100 - 70
        assert has_blocker is True
        assert has_critical is False

    def test_critical_deduction(self) -> None:
        findings = [{"severity": "critical"}]
        score, has_blocker, has_critical = calculate_format_score(findings)
        assert score == 75  # 100 - 25
        assert has_blocker is False
        assert has_critical is True

    def test_warning_deduction(self) -> None:
        findings = [{"severity": "warning"}]
        score, has_blocker, has_critical = calculate_format_score(findings)
        assert score == 92  # 100 - 8

    def test_info_deduction(self) -> None:
        findings = [{"severity": "info"}]
        score, has_blocker, has_critical = calculate_format_score(findings)
        assert score == 97  # 100 - 3

    def test_floor_at_zero(self) -> None:
        # Multiple blockers and criticals
        findings = [
            {"severity": "blocker"},
            {"severity": "blocker"},
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "critical"},
        ]
        score, has_blocker, has_critical = calculate_format_score(findings)
        assert score == 0

    def test_mixed_findings(self) -> None:
        findings = [
            {"severity": "warning"},
            {"severity": "warning"},
            {"severity": "info"},
        ]
        # 100 - 8 - 8 - 3 = 81
        score, _, _ = calculate_format_score(findings)
        assert score == 81


# ---------------------------------------------------------------------------
# TestRunAllRules
# ---------------------------------------------------------------------------


class TestRunAllRules:
    def test_returns_list_of_findings(self) -> None:
        resume = _make_resume()
        findings = run_all_rules(resume)
        assert isinstance(findings, list)

    def test_each_finding_has_id(self) -> None:
        # Use a resume with some issues to generate findings
        resume = _make_resume(
            raw_text=_SAMPLE_RAW_TEXT + "\n► Fancy bullet\nhttps://linkedin.com/in/johndoe",
            file_size=3_000_000,
        )
        findings = run_all_rules(resume)
        for finding in findings:
            assert "id" in finding
            assert finding["id"]  # non-empty

    def test_clean_resume_has_few_or_no_findings(self) -> None:
        resume = _make_resume()
        findings = run_all_rules(resume)
        # A clean resume should have no blockers or criticals
        severities = {f["severity"] for f in findings}
        assert "blocker" not in severities
        assert "critical" not in severities

    def test_blocker_short_circuits_text_rules(self) -> None:
        # Empty text with large file triggers blocker → text-dependent rules skipped
        resume = _make_resume(raw_text="", file_size=500_000, file_type="pdf")
        findings = run_all_rules(resume)
        blockers = [f for f in findings if f["severity"] == "blocker"]
        assert len(blockers) >= 1
        # No rules that require text content should have fired (e.g., contact info)
        rule_ids = {f["rule_id"] for f in findings}
        # Contact info check (rule_id: "contact_info") requires text analysis — should be skipped
        assert "contact_info" not in rule_ids
        assert "standard_sections" not in rule_ids

    def test_run_all_rules_normal_resume(self) -> None:
        """Run against a full normal resume — should return a list without errors."""
        resume = _make_resume()
        findings = run_all_rules(resume)
        assert isinstance(findings, list)
        # All findings should have required fields
        for f in findings:
            assert "id" in f
            assert "rule_id" in f
            assert "severity" in f
            assert "category" in f
            assert f["category"] == "format"
            assert "dismissed" in f
            assert f["dismissed"] is False
