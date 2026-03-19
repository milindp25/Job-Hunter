from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ResumeData:
    """Structured resume data for template rendering."""

    full_name: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None
    skills: list[str] = field(default_factory=list)
    experience: list[dict[str, str | None]] = field(default_factory=list)
    education: list[dict[str, str | None]] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)


@runtime_checkable
class ResumeTemplate(Protocol):
    """Protocol that all resume templates must implement."""

    @property
    def template_id(self) -> str: ...

    @property
    def template_name(self) -> str: ...

    @property
    def description(self) -> str: ...

    def render(self, data: ResumeData, accent_color: str | None = None) -> bytes: ...


class TemplateRegistry:
    """Central registry for available resume templates."""

    _templates: dict[str, ResumeTemplate] = {}

    @classmethod
    def register(cls, template: ResumeTemplate) -> None:
        """Register a template instance."""
        cls._templates[template.template_id] = template

    @classmethod
    def get_template(cls, template_id: str) -> ResumeTemplate | None:
        """Look up a template by its ID."""
        return cls._templates.get(template_id)

    @classmethod
    def list_templates(cls) -> list[dict[str, str]]:
        """Return metadata for all registered templates."""
        return [
            {
                "id": t.template_id,
                "name": t.template_name,
                "description": t.description,
            }
            for t in cls._templates.values()
        ]
