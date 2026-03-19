from __future__ import annotations

import io
from typing import TYPE_CHECKING

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

if TYPE_CHECKING:
    from app.services.resume_templates.base import ResumeData

_DEFAULT_ACCENT = "#374151"


class MinimalTemplate:
    """Clean, minimal resume layout with generous whitespace."""

    @property
    def template_id(self) -> str:
        return "minimal"

    @property
    def template_name(self) -> str:
        return "Minimal"

    @property
    def description(self) -> str:
        return "Clean single-column layout with generous whitespace and thin dividers."

    def render(self, data: ResumeData, accent_color: str | None = None) -> bytes:
        accent = accent_color or _DEFAULT_ACCENT
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=1.0 * inch,
            rightMargin=1.0 * inch,
            topMargin=0.8 * inch,
            bottomMargin=0.8 * inch,
        )

        styles = _build_styles(accent)
        story: list[object] = []

        # --- Name ---
        if data.full_name:
            story.append(Paragraph(data.full_name, styles["Name"]))
            story.append(Spacer(1, 4))

        # Contact line
        parts: list[str] = []
        if data.email:
            parts.append(data.email)
        if data.phone:
            parts.append(data.phone)
        if data.location:
            parts.append(data.location)
        if parts:
            story.append(Paragraph("  \u00b7  ".join(parts), styles["Contact"]))

        links: list[str] = []
        if data.linkedin_url:
            links.append(data.linkedin_url)
        if data.github_url:
            links.append(data.github_url)
        if data.portfolio_url:
            links.append(data.portfolio_url)
        if links:
            story.append(Paragraph("  \u00b7  ".join(links), styles["Contact"]))

        story.append(Spacer(1, 10))
        story.append(_thin_rule(accent))
        story.append(Spacer(1, 10))

        # --- Summary ---
        if data.summary:
            story.append(Paragraph(data.summary, styles["Body"]))
            story.append(Spacer(1, 10))
            story.append(_thin_rule(accent))
            story.append(Spacer(1, 10))

        # --- Experience ---
        if data.experience:
            story.append(Paragraph("Experience", styles["SectionHeading"]))
            story.append(Spacer(1, 6))
            for exp in data.experience:
                _add_experience(story, exp, styles)
            story.append(_thin_rule(accent))
            story.append(Spacer(1, 10))

        # --- Education ---
        if data.education:
            story.append(Paragraph("Education", styles["SectionHeading"]))
            story.append(Spacer(1, 6))
            for edu in data.education:
                _add_education(story, edu, styles)
            story.append(_thin_rule(accent))
            story.append(Spacer(1, 10))

        # --- Skills ---
        if data.skills:
            story.append(Paragraph("Skills", styles["SectionHeading"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph(", ".join(data.skills), styles["Body"]))
            story.append(Spacer(1, 10))

        # --- Certifications ---
        if data.certifications:
            story.append(Paragraph("Certifications", styles["SectionHeading"]))
            story.append(Spacer(1, 6))
            for cert in data.certifications:
                story.append(Paragraph(cert, styles["Body"]))
            story.append(Spacer(1, 10))

        # --- Languages ---
        if data.languages:
            story.append(Paragraph("Languages", styles["SectionHeading"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph(", ".join(data.languages), styles["Body"]))

        doc.build(story)  # type: ignore[arg-type]
        return buf.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _thin_rule(accent: str) -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=HexColor(accent), spaceAfter=0)


def _build_styles(accent: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    color = HexColor(accent)

    return {
        "Name": ParagraphStyle(
            "Name",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=color,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "Contact": ParagraphStyle(
            "Contact",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=HexColor("#666666"),
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=color,
            spaceAfter=0,
            spaceBefore=0,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=HexColor("#333333"),
        ),
        "EntryTitle": ParagraphStyle(
            "EntryTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=HexColor("#222222"),
        ),
        "EntrySubtitle": ParagraphStyle(
            "EntrySubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=HexColor("#888888"),
        ),
    }


def _add_experience(
    story: list[object],
    exp: dict[str, str | None],
    styles: dict[str, ParagraphStyle],
) -> None:
    title = exp.get("title") or exp.get("position") or ""
    company = exp.get("company") or ""
    dates = exp.get("dates") or exp.get("date_range") or ""
    raw = exp.get("raw")

    if title or company:
        header = title + (f" — {company}" if company else "")
        story.append(Paragraph(header, styles["EntryTitle"]))
        if dates:
            story.append(Paragraph(dates, styles["EntrySubtitle"]))
    elif raw:
        for line in str(raw).splitlines():
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["Body"]))

    desc = exp.get("description") or exp.get("responsibilities")
    if desc:
        for line in str(desc).splitlines():
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["Body"]))

    story.append(Spacer(1, 8))


def _add_education(
    story: list[object],
    edu: dict[str, str | None],
    styles: dict[str, ParagraphStyle],
) -> None:
    degree = edu.get("degree") or ""
    school = edu.get("school") or edu.get("institution") or ""
    dates = edu.get("dates") or edu.get("graduation_date") or ""
    raw = edu.get("raw")

    if degree or school:
        header = degree + (f" — {school}" if school else "")
        story.append(Paragraph(header, styles["EntryTitle"]))
        if dates:
            story.append(Paragraph(dates, styles["EntrySubtitle"]))
    elif raw:
        for line in str(raw).splitlines():
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["Body"]))

    story.append(Spacer(1, 6))
