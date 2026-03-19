"""ATS Format Compliance Rule Engine.

16 deterministic format checks with zero API cost.
Each rule receives a resume object and returns a finding dict or None.
"""

from __future__ import annotations

import re
import uuid
from typing import Any  # noqa: TCH003

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_finding(
    rule_id: str,
    severity: str,
    confidence: str,
    title: str,
    detail: str,
    suggestion: str,
    section: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a normalised finding dict."""
    finding: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "rule_id": rule_id,
        "category": "format",
        "severity": severity,
        "confidence": confidence,
        "title": title,
        "detail": detail,
        "suggestion": suggestion,
        "dismissed": False,
    }
    if section is not None:
        finding["section"] = section
    if metadata is not None:
        finding["metadata"] = metadata
    return finding


def _get_str(obj: object, attr: str) -> str:
    """Safely retrieve a string attribute from the resume-like object."""
    value = getattr(obj, attr, None)
    return value if isinstance(value, str) else ""


def _get_int(obj: object, attr: str, default: int = 0) -> int:
    """Safely retrieve an int attribute from the resume-like object."""
    value = getattr(obj, attr, None)
    return value if isinstance(value, int) else default


def _get_dict(obj: object, attr: str) -> dict[str, Any]:
    """Safely retrieve a dict attribute from the resume-like object."""
    value = getattr(obj, attr, None)
    return value if isinstance(value, dict) else {}


# ---------------------------------------------------------------------------
# Rule 1: Parseable text
# ---------------------------------------------------------------------------


def check_parseable_text(resume: object) -> dict[str, Any] | None:
    """Detect image-only or encrypted PDFs that extracted no usable text."""
    raw_text = _get_str(resume, "raw_text")
    file_size = _get_int(resume, "file_size")

    stripped = raw_text.strip()
    if len(stripped) < 50 and file_size > 10_000:
        return _make_finding(
            rule_id="parseable_text",
            severity="blocker",
            confidence="high",
            title="Resume text could not be extracted",
            detail=(
                f"Only {len(stripped)} characters were extracted from a "
                f"{file_size:,}-byte file. The file is likely scanned, image-based, "
                "or encrypted — ATS systems cannot read it."
            ),
            suggestion=(
                "Export your resume as a text-based PDF from a word processor "
                "(Word, Google Docs) rather than scanning a printed copy."
            ),
        )
    return None


# ---------------------------------------------------------------------------
# Rule 2: Text quality
# ---------------------------------------------------------------------------

_NON_WORD_RE = re.compile(r"[^\w\s]")


def check_text_quality(resume: object) -> dict[str, Any] | None:
    """Flag garbled extraction: >20% non-word characters."""
    raw_text = _get_str(resume, "raw_text")
    if not raw_text:
        return None

    total = len(raw_text)
    non_word_count = len(_NON_WORD_RE.findall(raw_text))
    ratio = non_word_count / total if total else 0.0

    if ratio > 0.20:
        pct = round(ratio * 100, 1)
        return _make_finding(
            rule_id="text_quality",
            severity="critical",
            confidence="high",
            title="Garbled or corrupted text detected",
            detail=(
                f"{pct}% of characters are non-word symbols, suggesting the PDF "
                "text layer is corrupted or heavily encoded."
            ),
            suggestion=(
                "Re-save your resume as a fresh PDF from Microsoft Word or Google Docs "
                "to ensure clean text extraction."
            ),
            metadata={"non_word_ratio": ratio},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 3: Tables
# ---------------------------------------------------------------------------

_TAB_RE = re.compile(r"\t")


def check_tables(resume: object) -> dict[str, Any] | None:
    """Detect tab-heavy lines indicating table usage (>3 tabs per line in >5% of lines)."""
    raw_text = _get_str(resume, "raw_text")
    if not raw_text:
        return None

    lines = raw_text.splitlines()
    if not lines:
        return None

    tab_heavy = sum(1 for line in lines if len(_TAB_RE.findall(line)) >= 3)
    ratio = tab_heavy / len(lines)

    if ratio > 0.05:
        return _make_finding(
            rule_id="tables",
            severity="critical",
            confidence="medium",
            title="Table formatting detected",
            detail=(
                f"Approximately {round(ratio * 100, 1)}% of lines contain 3 or more "
                "tab characters, suggesting table-based layout. Most ATS systems "
                "cannot parse tables correctly."
            ),
            suggestion=(
                "Replace tables with simple bullet-point lists and plain text sections."
            ),
            metadata={"tab_heavy_line_ratio": ratio},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 4: Multi-column layout
# ---------------------------------------------------------------------------

_LARGE_GAP_RE = re.compile(r"\S {5,}\S")


def check_multi_column(resume: object) -> dict[str, Any] | None:
    """Detect multi-column layout via large mid-line whitespace gaps in >10% of lines."""
    raw_text = _get_str(resume, "raw_text")
    if not raw_text:
        return None

    lines = [line for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return None

    gap_lines = sum(1 for line in lines if _LARGE_GAP_RE.search(line))
    ratio = gap_lines / len(lines)

    if ratio > 0.10:
        return _make_finding(
            rule_id="multi_column",
            severity="critical",
            confidence="medium",
            title="Multi-column layout detected",
            detail=(
                f"Approximately {round(ratio * 100, 1)}% of non-empty lines contain "
                "large whitespace gaps consistent with a two-column layout. "
                "ATS systems read left-to-right and will scramble column content."
            ),
            suggestion=(
                "Convert your resume to a single-column format for reliable ATS parsing."
            ),
            metadata={"gap_line_ratio": ratio},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 5: Standard sections
# ---------------------------------------------------------------------------

_EXPERIENCE_RE = re.compile(
    r"\b(experience|work history|employment|work experience)\b", re.IGNORECASE
)
_EDUCATION_RE = re.compile(
    r"\b(education|academic|degree|university|college)\b", re.IGNORECASE
)
_SKILLS_RE = re.compile(
    r"\b(skills|technical skills|competencies|expertise|technologies)\b", re.IGNORECASE
)


def check_standard_sections(resume: object) -> dict[str, Any] | None:
    """Warn when standard resume sections are absent."""
    raw_text = _get_str(resume, "raw_text")

    missing: list[str] = []
    if not _EXPERIENCE_RE.search(raw_text):
        missing.append("Experience")
    if not _EDUCATION_RE.search(raw_text):
        missing.append("Education")
    if not _SKILLS_RE.search(raw_text):
        missing.append("Skills")

    if missing:
        joined = ", ".join(missing)
        return _make_finding(
            rule_id="standard_sections",
            severity="warning",
            confidence="high",
            title=f"Missing standard section(s): {joined}",
            detail=(
                f"The following sections were not detected: {joined}. "
                "ATS systems use section headers to categorise your content."
            ),
            suggestion=(
                f"Add clearly labelled '{missing[0]}' (and other missing) sections "
                "with standard header names."
            ),
            metadata={"missing_sections": missing},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 6: Contact info
# ---------------------------------------------------------------------------


def check_contact_info(resume: object) -> dict[str, Any] | None:
    """Warn when key contact fields are absent from parsed data."""
    parsed_data = _get_dict(resume, "parsed_data")

    missing: list[str] = []
    if not parsed_data.get("full_name"):
        missing.append("name")
    if not parsed_data.get("email"):
        missing.append("email address")
    if not parsed_data.get("phone"):
        missing.append("phone number")

    if missing:
        joined = " and ".join(missing)
        return _make_finding(
            rule_id="contact_info",
            severity="warning",
            confidence="high",
            title=f"Missing contact information: {joined}",
            detail=(
                f"Your resume is missing: {joined}. "
                "Recruiters and ATS systems need complete contact details."
            ),
            suggestion=f"Add your {joined} prominently at the top of your resume.",
            metadata={"missing_fields": missing},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 7: Resume length
# ---------------------------------------------------------------------------


def check_resume_length(resume: object) -> dict[str, Any] | None:
    """Flag resumes that are suspiciously short (<100 words) or very long (>1500 words)."""
    raw_text = _get_str(resume, "raw_text")
    word_count = len(raw_text.split())

    if word_count < 100:
        return _make_finding(
            rule_id="resume_length",
            severity="warning",
            confidence="high",
            title="Resume appears too short",
            detail=(
                f"Your resume contains only {word_count} words. "
                "Most ATS systems expect 300–800 words for a one-page resume."
            ),
            suggestion=(
                "Expand your experience descriptions, add bullet points, "
                "and ensure all relevant sections are present."
            ),
            metadata={"word_count": word_count},
        )

    if word_count > 1500:
        return _make_finding(
            rule_id="resume_length",
            severity="warning",
            confidence="high",
            title="Resume may be too long",
            detail=(
                f"Your resume contains {word_count} words. "
                "Resumes over ~1500 words (roughly 2+ pages) may be truncated by ATS systems."
            ),
            suggestion=(
                "Trim older or less relevant experience to keep your resume "
                "concise and focused."
            ),
            metadata={"word_count": word_count},
        )

    return None


# ---------------------------------------------------------------------------
# Rule 8: File size
# ---------------------------------------------------------------------------

_TWO_MB = 2_097_152  # 2 × 1024 × 1024


def check_file_size(resume: object) -> dict[str, Any] | None:
    """Inform when file exceeds 2 MB — some portals reject larger uploads."""
    file_size = _get_int(resume, "file_size")

    if file_size > _TWO_MB:
        size_mb = round(file_size / 1_048_576, 2)
        return _make_finding(
            rule_id="file_size",
            severity="info",
            confidence="high",
            title="File size exceeds 2 MB",
            detail=(
                f"Your resume file is {size_mb} MB. Some ATS portals reject files "
                "larger than 2 MB."
            ),
            suggestion=(
                "Compress images or export as a smaller PDF. "
                "Target under 1 MB for widest compatibility."
            ),
            metadata={"file_size_bytes": file_size, "file_size_mb": size_mb},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 9: Header/footer contact info
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"\+?[\d][\d\s\-().]{7,}\d")


def check_header_footer_info(resume: object) -> dict[str, Any] | None:
    """Warn if contact info appears only in the header/footer region (first/last 2 lines)."""
    raw_text = _get_str(resume, "raw_text")
    lines = [line for line in raw_text.splitlines() if line.strip()]
    if len(lines) < 5:
        return None

    # Check whether contact info exists at all
    has_email = bool(_EMAIL_RE.search(raw_text))
    has_phone = bool(_PHONE_RE.search(raw_text))
    if not has_email and not has_phone:
        return None  # contact_info rule will catch this

    # Body = middle lines (excluding first 2 and last 2)
    body_lines = lines[2:-2]
    body_text = "\n".join(body_lines)
    body_has_email = bool(_EMAIL_RE.search(body_text))
    body_has_phone = bool(_PHONE_RE.search(body_text))

    if (has_email and not body_has_email) or (has_phone and not body_has_phone):
        return _make_finding(
            rule_id="header_footer_info",
            severity="warning",
            confidence="medium",
            title="Contact information may be in header/footer only",
            detail=(
                "Contact details appear to be placed only in the document's "
                "header or footer region. Many ATS systems skip header/footer content."
            ),
            suggestion=(
                "Place your name, email, and phone number in the main body "
                "of the document at the very top, not in the header/footer."
            ),
        )
    return None


# ---------------------------------------------------------------------------
# Rule 10: Bullet characters
# ---------------------------------------------------------------------------

_FANCY_BULLET_RE = re.compile(r"[►★➤➜➡▶◆◇■□▪▸‣⁃]")


def check_bullet_characters(resume: object) -> dict[str, Any] | None:
    """Warn when non-standard bullet characters are present."""
    raw_text = _get_str(resume, "raw_text")
    matches = _FANCY_BULLET_RE.findall(raw_text)

    if matches:
        unique = list({m for m in matches})
        return _make_finding(
            rule_id="bullet_characters",
            severity="warning",
            confidence="medium",
            title="Non-standard bullet characters detected",
            detail=(
                f"Found special bullet characters: {' '.join(unique)}. "
                "These may be stripped or cause encoding issues in ATS systems."
            ),
            suggestion=(
                "Replace fancy bullets with standard ASCII hyphens (-) "
                "or Unicode bullet points (•)."
            ),
            metadata={"found_characters": unique},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 11: Date consistency
# ---------------------------------------------------------------------------

_DATE_FORMATS: dict[str, re.Pattern[str]] = {
    "MM/YYYY": re.compile(r"\b\d{2}/\d{4}\b"),
    "Mon YYYY": re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
        re.IGNORECASE,
    ),
    "YYYY": re.compile(r"\b(19|20)\d{2}\b"),
}


def check_date_consistency(resume: object) -> dict[str, Any] | None:
    """Warn when multiple incompatible date formats are mixed across the resume."""
    raw_text = _get_str(resume, "raw_text")

    present_formats: list[str] = []
    for fmt_name, pattern in _DATE_FORMATS.items():
        if pattern.search(raw_text):
            present_formats.append(fmt_name)

    # "YYYY" alone is always present if Mon YYYY or MM/YYYY is — exclude bare year from mix check
    # Only warn if named formats are inconsistent (e.g., MM/YYYY alongside Mon YYYY)
    named_formats = [f for f in present_formats if f != "YYYY"]
    if len(named_formats) > 1:
        return _make_finding(
            rule_id="date_consistency",
            severity="warning",
            confidence="medium",
            title="Inconsistent date formats detected",
            detail=(
                f"Multiple date formats found: {', '.join(named_formats)}. "
                "Inconsistent formatting can confuse ATS date parsers."
            ),
            suggestion=(
                "Use a single consistent date format throughout your resume, "
                "e.g., 'Jan 2020' or '01/2020'."
            ),
            metadata={"detected_formats": named_formats},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 12: Chronological order
# ---------------------------------------------------------------------------

_YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")
_EXPERIENCE_SECTION_RE = re.compile(
    r"\b(experience|work history|employment|work experience)\b.*",
    re.IGNORECASE | re.DOTALL,
)


def check_chronological_order(resume: object) -> dict[str, Any] | None:
    """Warn when experience years are not in descending (reverse-chrono) order."""
    raw_text = _get_str(resume, "raw_text")

    # Extract the experience section
    match = _EXPERIENCE_SECTION_RE.search(raw_text)
    section_text = match.group(0) if match else raw_text

    years = [int(y) for y in _YEAR_RE.findall(section_text)]
    if len(years) < 2:
        return None

    # Check if years are in descending order
    is_descending = all(years[i] >= years[i + 1] for i in range(len(years) - 1))
    if not is_descending:
        return _make_finding(
            rule_id="chronological_order",
            severity="warning",
            confidence="medium",
            title="Experience may not be in reverse chronological order",
            detail=(
                "The years extracted from the experience section do not appear "
                "to be in descending order. ATS systems and recruiters expect "
                "the most recent position first."
            ),
            suggestion=(
                "Reorder your experience entries so the most recent position "
                "appears at the top."
            ),
            metadata={"detected_years": years},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 13: Embedded images
# ---------------------------------------------------------------------------

_IMAGE_BYTES_PER_CHAR_THRESHOLD = 50


def check_embedded_images(resume: object) -> dict[str, Any] | None:
    """Warn when the bytes-per-character ratio suggests embedded images."""
    file_size = _get_int(resume, "file_size")
    raw_text = _get_str(resume, "raw_text")
    char_count = len(raw_text)

    if char_count == 0:
        return None  # parseable_text blocker handles this

    ratio = file_size / char_count
    if ratio > _IMAGE_BYTES_PER_CHAR_THRESHOLD:
        return _make_finding(
            rule_id="embedded_images",
            severity="warning",
            confidence="high",
            title="Embedded images may be present",
            detail=(
                f"The file is {file_size:,} bytes but contains only {char_count} "
                f"characters of text ({ratio:.0f} bytes/char). Embedded images inflate "
                "file size and cannot be parsed by ATS systems."
            ),
            suggestion=(
                "Remove photos, logos, or other images from your resume. "
                "ATS systems cannot read visual content."
            ),
            metadata={"bytes_per_char": ratio},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 14: Font detection (PDF-only marker)
# ---------------------------------------------------------------------------


def check_font_detection(resume: object) -> dict[str, Any] | None:
    """Low-confidence info note — font analysis requires deeper PDF inspection."""
    file_type = _get_str(resume, "file_type")
    if file_type != "pdf":
        return None

    return _make_finding(
        rule_id="font_detection",
        severity="info",
        confidence="low",
        title="Font embedding not verified",
        detail=(
            "Full font embedding verification requires PDF-level inspection beyond "
            "text extraction. Non-embedded fonts may render incorrectly in some ATS."
        ),
        suggestion=(
            "When saving your PDF, choose 'Embed all fonts' in your PDF export settings "
            "to ensure consistent rendering."
        ),
    )


# ---------------------------------------------------------------------------
# Rule 15: Hyperlink formatting
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+")


def check_hyperlink_formatting(resume: object) -> dict[str, Any] | None:
    """Info note when raw URLs are present — some ATS truncate or break them."""
    raw_text = _get_str(resume, "raw_text")
    matches = _URL_RE.findall(raw_text)

    if matches:
        return _make_finding(
            rule_id="hyperlink_formatting",
            severity="info",
            confidence="low",
            title="Raw URLs detected in resume",
            detail=(
                f"Found {len(matches)} URL(s). Some ATS systems break or truncate "
                "long URLs, especially when hyperlinking is unsupported."
            ),
            suggestion=(
                "Keep URLs short (e.g., linkedin.com/in/yourname) and avoid "
                "long tracking URLs or URL shorteners."
            ),
            metadata={"url_count": len(matches), "sample_urls": matches[:3]},
        )
    return None


# ---------------------------------------------------------------------------
# Rule 16: Text boxes (DOCX-specific)
# ---------------------------------------------------------------------------


def check_text_boxes(resume: object) -> dict[str, Any] | None:
    """Critical note for DOCX files about text box limitations."""
    file_type = _get_str(resume, "file_type")
    if file_type != "docx":
        return None

    return _make_finding(
        rule_id="text_boxes",
        severity="critical",
        confidence="medium",
        title="DOCX format: text boxes cannot be verified",
        detail=(
            "Microsoft Word documents can contain text boxes whose content is "
            "invisible to ATS parsers. Content inside text boxes is commonly lost."
        ),
        suggestion=(
            "Open your Word document and ensure all content is in the main body — "
            "not in text boxes, shapes, or drawing objects. "
            "Alternatively, export to PDF."
        ),
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

# Rules that require readable text to be meaningful
_TEXT_DEPENDENT_RULES = [
    check_text_quality,
    check_tables,
    check_multi_column,
    check_standard_sections,
    check_contact_info,
    check_resume_length,
    check_header_footer_info,
    check_bullet_characters,
    check_date_consistency,
    check_chronological_order,
]



def run_all_rules(resume: object) -> list[dict[str, Any]]:
    """Run all 16 format rules and return a list of findings.

    Short-circuit behaviour: if ``check_parseable_text`` returns a blocker,
    skip the text-dependent rules and only run structural checks.
    """
    findings: list[dict[str, Any]] = []

    parseable_finding = check_parseable_text(resume)
    if parseable_finding is not None:
        findings.append(parseable_finding)
        # Short-circuit: skip text-dependent rules
        structural = [
            check_file_size,
            check_embedded_images,
            check_text_boxes,
        ]
        for rule_fn in structural:
            result = rule_fn(resume)
            if result is not None:
                findings.append(result)
        return findings

    # All rules (text-dependent + structural)
    all_rules = [
        check_text_quality,
        check_tables,
        check_multi_column,
        check_standard_sections,
        check_contact_info,
        check_resume_length,
        check_file_size,
        check_header_footer_info,
        check_bullet_characters,
        check_date_consistency,
        check_chronological_order,
        check_embedded_images,
        check_font_detection,
        check_hyperlink_formatting,
        check_text_boxes,
    ]

    for rule_fn in all_rules:
        result = rule_fn(resume)
        if result is not None:
            findings.append(result)

    return findings


# ---------------------------------------------------------------------------
# Score calculator
# ---------------------------------------------------------------------------

_SEVERITY_DEDUCTIONS: dict[str, int] = {
    "blocker": 70,
    "critical": 25,
    "warning": 8,
    "info": 3,
}


def calculate_format_score(findings: list[dict[str, Any]]) -> tuple[int, bool, bool]:
    """Calculate an ATS format compliance score from a list of findings.

    Args:
        findings: List of finding dicts (each with a ``severity`` key).

    Returns:
        A tuple of (score, has_blocker, has_critical) where score is in [0, 100].
    """
    score = 100
    has_blocker = False
    has_critical = False

    for finding in findings:
        severity = finding.get("severity", "")
        deduction = _SEVERITY_DEDUCTIONS.get(severity, 0)
        score -= deduction
        if severity == "blocker":
            has_blocker = True
        elif severity == "critical":
            has_critical = True

    score = max(0, score)
    return score, has_blocker, has_critical
