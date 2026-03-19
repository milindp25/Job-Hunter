from __future__ import annotations

import io
from typing import TYPE_CHECKING

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

_DEFAULT_ACCENT = "#1a1a2e"


class ClassicTemplate:
    """Professional single-column resume layout with Helvetica fonts."""

    @property
    def template_id(self) -> str:
        return "classic"

    @property
    def template_name(self) -> str:
        return "Classic"

    @property
    def description(self) -> str:
        return "Professional single-column layout with clean typography and horizontal rules."

    def render(self, data: ResumeData, accent_color: str | None = None) -> bytes:
        accent = accent_color or _DEFAULT_ACCENT
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )

        styles = _build_styles(accent)
        story: list[object] = []

        # --- Header ---
        if data.full_name:
            story.append(Paragraph(data.full_name, styles["Name"]))

        contact_parts: list[str] = []
        if data.email:
            contact_parts.append(data.email)
        if data.phone:
            contact_parts.append(data.phone)
        if data.location:
            contact_parts.append(data.location)
        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), styles["Contact"]))

        link_parts: list[str] = []
        if data.linkedin_url:
            link_parts.append(data.linkedin_url)
        if data.github_url:
            link_parts.append(data.github_url)
        if data.portfolio_url:
            link_parts.append(data.portfolio_url)
        if link_parts:
            story.append(Paragraph(" | ".join(link_parts), styles["Contact"]))

        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor(accent)))
        story.append(Spacer(1, 8))

        # --- Summary ---
        if data.summary:
            story.append(Paragraph("SUMMARY", styles["SectionHeading"]))
            story.append(Spacer(1, 4))
            story.append(Paragraph(data.summary, styles["Body"]))
            story.append(Spacer(1, 10))

        # --- Experience ---
        if data.experience:
            story.append(Paragraph("EXPERIENCE", styles["SectionHeading"]))
            story.append(Spacer(1, 4))
            for exp in data.experience:
                _add_experience_entry(story, exp, styles)
            story.append(Spacer(1, 6))

        # --- Education ---
        if data.education:
            story.append(Paragraph("EDUCATION", styles["SectionHeading"]))
            story.append(Spacer(1, 4))
            for edu in data.education:
                _add_education_entry(story, edu, styles)
            story.append(Spacer(1, 6))

        # --- Skills ---
        if data.skills:
            story.append(Paragraph("SKILLS", styles["SectionHeading"]))
            story.append(Spacer(1, 4))
            story.append(Paragraph(", ".join(data.skills), styles["Body"]))
            story.append(Spacer(1, 10))

        # --- Certifications ---
        if data.certifications:
            story.append(Paragraph("CERTIFICATIONS", styles["SectionHeading"]))
            story.append(Spacer(1, 4))
            for cert in data.certifications:
                story.append(Paragraph(f"\u2022 {cert}", styles["Bullet"]))
            story.append(Spacer(1, 10))

        # --- Languages ---
        if data.languages:
            story.append(Paragraph("LANGUAGES", styles["SectionHeading"]))
            story.append(Spacer(1, 4))
            story.append(Paragraph(", ".join(data.languages), styles["Body"]))

        doc.build(story)  # type: ignore[arg-type]
        return buf.getvalue()


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------


def _build_styles(accent: str) -> dict[str, ParagraphStyle]:
    """Build paragraph styles for the classic template."""
    base = getSampleStyleSheet()
    color = HexColor(accent)

    return {
        "Name": ParagraphStyle(
            "Name",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=color,
            spaceAfter=2,
        ),
        "Contact": ParagraphStyle(
            "Contact",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=HexColor("#444444"),
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=color,
            spaceAfter=2,
            spaceBefore=4,
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
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=HexColor("#555555"),
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            alignment=TA_LEFT,
            textColor=HexColor("#333333"),
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            leftIndent=12,
            textColor=HexColor("#333333"),
        ),
    }


def _add_experience_entry(
    story: list[object],
    exp: dict[str, str | None],
    styles: dict[str, ParagraphStyle],
) -> None:
    """Append a single experience entry to the story."""
    title = exp.get("title") or exp.get("position") or ""
    company = exp.get("company") or ""
    dates = exp.get("dates") or exp.get("date_range") or ""
    raw = exp.get("raw")

    if title or company:
        header = f"{title}" + (f" at {company}" if company else "")
        story.append(Paragraph(header, styles["EntryTitle"]))
        if dates:
            story.append(Paragraph(dates, styles["EntrySubtitle"]))
    elif raw:
        # Fallback: render raw text block
        for line in str(raw).splitlines():
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["Body"]))

    description = exp.get("description") or exp.get("responsibilities")
    if description:
        for line in str(description).splitlines():
            line = line.strip()
            if line:
                story.append(Paragraph(f"\u2022 {line}", styles["Bullet"]))

    story.append(Spacer(1, 6))


def _add_education_entry(
    story: list[object],
    edu: dict[str, str | None],
    styles: dict[str, ParagraphStyle],
) -> None:
    """Append a single education entry to the story."""
    degree = edu.get("degree") or ""
    school = edu.get("school") or edu.get("institution") or ""
    dates = edu.get("dates") or edu.get("graduation_date") or ""
    raw = edu.get("raw")

    if degree or school:
        header = degree + (f" - {school}" if school else "")
        story.append(Paragraph(header, styles["EntryTitle"]))
        if dates:
            story.append(Paragraph(dates, styles["EntrySubtitle"]))
    elif raw:
        for line in str(raw).splitlines():
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["Body"]))

    story.append(Spacer(1, 4))
