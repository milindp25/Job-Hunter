from __future__ import annotations

import io
from typing import TYPE_CHECKING

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

if TYPE_CHECKING:
    from app.services.resume_templates.base import ResumeData

_DEFAULT_ACCENT = "#2563EB"


class ModernTemplate:
    """Two-column resume layout with a coloured left sidebar."""

    @property
    def template_id(self) -> str:
        return "modern"

    @property
    def template_name(self) -> str:
        return "Modern"

    @property
    def description(self) -> str:
        return "Two-column layout with a coloured sidebar for contact info, skills, and languages."

    def render(self, data: ResumeData, accent_color: str | None = None) -> bytes:
        accent = accent_color or _DEFAULT_ACCENT
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=0.4 * inch,
            rightMargin=0.4 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        styles = _build_styles(accent)

        # Build sidebar content (left column)
        sidebar: list[object] = []
        sidebar.append(Spacer(1, 8))

        # Contact
        sidebar.append(Paragraph("CONTACT", styles["SidebarHeading"]))
        sidebar.append(Spacer(1, 4))
        if data.email:
            sidebar.append(Paragraph(data.email, styles["SidebarBody"]))
        if data.phone:
            sidebar.append(Paragraph(data.phone, styles["SidebarBody"]))
        if data.location:
            sidebar.append(Paragraph(data.location, styles["SidebarBody"]))
        if data.linkedin_url:
            sidebar.append(Paragraph(data.linkedin_url, styles["SidebarBody"]))
        if data.github_url:
            sidebar.append(Paragraph(data.github_url, styles["SidebarBody"]))
        if data.portfolio_url:
            sidebar.append(Paragraph(data.portfolio_url, styles["SidebarBody"]))
        sidebar.append(Spacer(1, 12))

        # Skills
        if data.skills:
            sidebar.append(Paragraph("SKILLS", styles["SidebarHeading"]))
            sidebar.append(Spacer(1, 4))
            for skill in data.skills:
                sidebar.append(Paragraph(f"\u2022 {skill}", styles["SidebarBullet"]))
            sidebar.append(Spacer(1, 12))

        # Languages
        if data.languages:
            sidebar.append(Paragraph("LANGUAGES", styles["SidebarHeading"]))
            sidebar.append(Spacer(1, 4))
            for lang in data.languages:
                sidebar.append(Paragraph(f"\u2022 {lang}", styles["SidebarBullet"]))
            sidebar.append(Spacer(1, 12))

        # Certifications
        if data.certifications:
            sidebar.append(Paragraph("CERTIFICATIONS", styles["SidebarHeading"]))
            sidebar.append(Spacer(1, 4))
            for cert in data.certifications:
                sidebar.append(Paragraph(f"\u2022 {cert}", styles["SidebarBullet"]))

        # Build main content (right column)
        main: list[object] = []
        main.append(Spacer(1, 4))

        if data.full_name:
            main.append(Paragraph(data.full_name, styles["Name"]))
            main.append(Spacer(1, 8))

        if data.summary:
            main.append(Paragraph("SUMMARY", styles["SectionHeading"]))
            main.append(Spacer(1, 4))
            main.append(Paragraph(data.summary, styles["Body"]))
            main.append(Spacer(1, 10))

        if data.experience:
            main.append(Paragraph("EXPERIENCE", styles["SectionHeading"]))
            main.append(Spacer(1, 4))
            for exp in data.experience:
                _add_experience(main, exp, styles)
            main.append(Spacer(1, 6))

        if data.education:
            main.append(Paragraph("EDUCATION", styles["SectionHeading"]))
            main.append(Spacer(1, 4))
            for edu in data.education:
                _add_education(main, edu, styles)

        # Combine into two-column table
        page_w = letter[0] - 0.8 * inch  # usable width
        sidebar_w = page_w * 0.30
        main_w = page_w * 0.70

        table_data = [[sidebar, main]]
        tbl = Table(table_data, colWidths=[sidebar_w, main_w])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), HexColor(accent)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (0, 0), 10),
                    ("RIGHTPADDING", (0, 0), (0, 0), 10),
                    ("LEFTPADDING", (1, 0), (1, 0), 14),
                    ("RIGHTPADDING", (1, 0), (1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        doc.build([tbl])
        return buf.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_styles(accent: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    color = HexColor(accent)

    return {
        "Name": ParagraphStyle(
            "Name",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=color,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=color,
            spaceAfter=2,
            spaceBefore=2,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
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
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=HexColor("#555555"),
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
        # Sidebar styles (white text on coloured background)
        "SidebarHeading": ParagraphStyle(
            "SidebarHeading",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=white,
            spaceAfter=2,
        ),
        "SidebarBody": ParagraphStyle(
            "SidebarBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=HexColor("#E0E0E0"),
        ),
        "SidebarBullet": ParagraphStyle(
            "SidebarBullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            leftIndent=8,
            textColor=HexColor("#E0E0E0"),
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
        header = title + (f" at {company}" if company else "")
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
                story.append(Paragraph(f"\u2022 {line}", styles["Bullet"]))

    story.append(Spacer(1, 6))


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
