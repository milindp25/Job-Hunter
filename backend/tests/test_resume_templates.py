from __future__ import annotations

import pytest

from app.services.resume_templates import (
    ClassicTemplate,
    MinimalTemplate,
    ModernTemplate,
    ResumeData,
    TemplateRegistry,
)


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestTemplateRegistry:
    def test_list_templates_returns_three(self) -> None:
        templates = TemplateRegistry.list_templates()
        assert len(templates) == 3

    def test_list_templates_have_required_keys(self) -> None:
        for t in TemplateRegistry.list_templates():
            assert "id" in t
            assert "name" in t
            assert "description" in t

    def test_get_classic_template(self) -> None:
        tpl = TemplateRegistry.get_template("classic")
        assert tpl is not None
        assert isinstance(tpl, ClassicTemplate)

    def test_get_modern_template(self) -> None:
        tpl = TemplateRegistry.get_template("modern")
        assert tpl is not None
        assert isinstance(tpl, ModernTemplate)

    def test_get_minimal_template(self) -> None:
        tpl = TemplateRegistry.get_template("minimal")
        assert tpl is not None
        assert isinstance(tpl, MinimalTemplate)

    def test_get_nonexistent_returns_none(self) -> None:
        assert TemplateRegistry.get_template("nonexistent") is None


# ---------------------------------------------------------------------------
# Template metadata tests
# ---------------------------------------------------------------------------


class TestTemplateMetadata:
    def test_classic_metadata(self) -> None:
        tpl = ClassicTemplate()
        assert tpl.template_id == "classic"
        assert tpl.template_name == "Classic"
        assert len(tpl.description) > 0

    def test_modern_metadata(self) -> None:
        tpl = ModernTemplate()
        assert tpl.template_id == "modern"
        assert tpl.template_name == "Modern"
        assert len(tpl.description) > 0

    def test_minimal_metadata(self) -> None:
        tpl = MinimalTemplate()
        assert tpl.template_id == "minimal"
        assert tpl.template_name == "Minimal"
        assert len(tpl.description) > 0


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------

_FULL_DATA = ResumeData(
    full_name="Jane Doe",
    email="jane@example.com",
    phone="555-123-4567",
    location="San Francisco, CA",
    linkedin_url="https://linkedin.com/in/janedoe",
    github_url="https://github.com/janedoe",
    portfolio_url="https://janedoe.dev",
    summary="Experienced software engineer with 8+ years in full-stack development.",
    skills=["Python", "TypeScript", "React", "PostgreSQL"],
    experience=[
        {
            "title": "Senior Engineer",
            "company": "Acme Corp",
            "dates": "2020 - Present",
            "description": "Led backend architecture.\nMentored junior developers.",
        },
    ],
    education=[
        {
            "degree": "B.S. Computer Science",
            "school": "MIT",
            "dates": "2012 - 2016",
        },
    ],
    certifications=["AWS Solutions Architect"],
    languages=["English", "Spanish"],
)

_MINIMAL_DATA = ResumeData()


@pytest.mark.parametrize("template_id", ["classic", "modern", "minimal"])
class TestTemplateRendering:
    def test_render_full_data_returns_pdf(self, template_id: str) -> None:
        tpl = TemplateRegistry.get_template(template_id)
        assert tpl is not None
        result = tpl.render(_FULL_DATA)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_render_minimal_data_returns_pdf(self, template_id: str) -> None:
        tpl = TemplateRegistry.get_template(template_id)
        assert tpl is not None
        result = tpl.render(_MINIMAL_DATA)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_render_with_accent_color(self, template_id: str) -> None:
        tpl = TemplateRegistry.get_template(template_id)
        assert tpl is not None
        result = tpl.render(_FULL_DATA, accent_color="#E11D48")
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_render_with_raw_experience(self, template_id: str) -> None:
        """Templates should handle the 'raw' fallback format from the parser."""
        data = ResumeData(
            full_name="John Smith",
            experience=[{"raw": "Software Engineer at Acme\n2020-2023"}],
            education=[{"raw": "BS CS — State University\nGraduated 2020"}],
        )
        tpl = TemplateRegistry.get_template(template_id)
        assert tpl is not None
        result = tpl.render(data)
        assert result[:5] == b"%PDF-"
