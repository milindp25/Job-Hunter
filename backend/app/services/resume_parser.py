from __future__ import annotations

import io
import re

import structlog

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

_PHONE_RE = re.compile(
    r"(?:\+?1[-.\s]?)?"           # optional country code
    r"(?:\(?\d{3}\)?[-.\s]?)"     # area code
    r"\d{3}[-.\s]?\d{4}"          # subscriber number
)

_SECTION_HEADINGS = re.compile(
    r"^[ \t]*("
    r"summary|objective|profile|about(?:\s+me)?"
    r"|experience|work\s+(?:experience|history)|employment"
    r"|education|academic"
    r"|skills|technical\s+skills|core\s+competencies"
    r"|certifications?|licenses?"
    r"|projects"
    r")[ \t]*:?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------


def _extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF bytes using pymupdf."""
    import fitz  # pymupdf

    text_parts: list[str] = []
    with fitz.open(stream=file_content, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def _extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(file_content))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------


def _split_sections(text: str) -> dict[str, str]:
    """Split resume text into named sections based on common headings.

    Returns a mapping of lowercase heading name to the text content that
    follows it (up to the next heading or end of text).  The special key
    ``"_preamble"`` holds any text before the first heading.
    """
    matches = list(_SECTION_HEADINGS.finditer(text))
    sections: dict[str, str] = {}

    if not matches:
        sections["_preamble"] = text
        return sections

    # Text before the first heading
    sections["_preamble"] = text[: matches[0].start()].strip()

    for i, match in enumerate(matches):
        heading = match.group(1).strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[heading] = text[start:end].strip()

    return sections


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------


def _extract_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> str | None:
    match = _PHONE_RE.search(text)
    return match.group(0).strip() if match else None


def _extract_name(text: str) -> str | None:
    """Best-effort name extraction: first non-empty line of the resume."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not _EMAIL_RE.search(stripped) and not _PHONE_RE.search(stripped):
            # Skip lines that look like section headings
            if _SECTION_HEADINGS.match(stripped):
                continue
            # Return cleaned name (no trailing colons etc.)
            return stripped.rstrip(":").strip()
    return None


def _extract_skills(section_text: str) -> list[str]:
    """Extract skill items from a skills section.

    Handles comma-separated, pipe-separated, and newline-separated lists.
    """
    # Try splitting by common delimiters first
    items: list[str] = []
    for line in section_text.splitlines():
        line = line.strip().lstrip("-*\u2022").strip()
        if not line:
            continue
        # Split on commas, pipes, or semicolons
        parts = re.split(r"[,|;]", line)
        for part in parts:
            cleaned = part.strip().lstrip("-*\u2022").strip()
            if cleaned:
                items.append(cleaned)

    return items


def _extract_summary(sections: dict[str, str]) -> str | None:
    """Find summary/objective section text."""
    for key in ("summary", "objective", "profile", "about me", "about"):
        if key in sections and sections[key]:
            return sections[key]
    return None


def _extract_experience(section_text: str) -> list[dict[str, str | None]]:
    """Basic extraction of experience entries.

    Returns a list of dicts with a ``raw`` key containing the text block
    for each entry.  A more sophisticated parser can be added later.
    """
    entries: list[dict[str, str | None]] = []
    if not section_text.strip():
        return entries

    # Split on blank lines to separate entries
    blocks = re.split(r"\n\s*\n", section_text.strip())
    for block in blocks:
        block = block.strip()
        if block:
            entries.append({"raw": block})

    return entries


def _extract_education(section_text: str) -> list[dict[str, str | None]]:
    """Basic extraction of education entries."""
    entries: list[dict[str, str | None]] = []
    if not section_text.strip():
        return entries

    blocks = re.split(r"\n\s*\n", section_text.strip())
    for block in blocks:
        block = block.strip()
        if block:
            entries.append({"raw": block})

    return entries


def _extract_certifications(section_text: str) -> list[str]:
    """Extract certification items from a certifications section."""
    items: list[str] = []
    for line in section_text.splitlines():
        cleaned = line.strip().lstrip("-*\u2022").strip()
        if cleaned:
            items.append(cleaned)
    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def parse_resume(file_content: bytes, filename: str) -> dict[
    str,
    str | None | list[str] | list[dict[str, str | None]],
]:
    """Parse a resume file and extract structured data.

    Args:
        file_content: Raw bytes of the uploaded file.
        filename: Original filename (used to determine file type).

    Returns:
        dict with keys: full_name, email, phone, location, summary,
        skills (list of skill names), experience (list of dicts),
        education (list of dicts), certifications (list of str).
    """
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        log.info("resume_parse_started", filename=filename, file_type="pdf")
        text = _extract_text_from_pdf(file_content)
    elif lower_name.endswith(".docx"):
        log.info("resume_parse_started", filename=filename, file_type="docx")
        text = _extract_text_from_docx(file_content)
    else:
        log.warning("resume_unsupported_format", filename=filename)
        raise ValueError(f"Unsupported file format: {filename}. Only PDF and DOCX are supported.")

    log.debug("resume_text_extracted", char_count=len(text))

    sections = _split_sections(text)

    # Extract fields
    full_name = _extract_name(text)
    email = _extract_email(text)
    phone = _extract_phone(text)
    summary = _extract_summary(sections)

    # Skills
    skills: list[str] = []
    for key in ("skills", "technical skills", "core competencies"):
        if key in sections:
            skills = _extract_skills(sections[key])
            break

    # Experience
    experience: list[dict[str, str | None]] = []
    for key in ("experience", "work experience", "work history", "employment"):
        if key in sections:
            experience = _extract_experience(sections[key])
            break

    # Education
    education: list[dict[str, str | None]] = []
    for key in ("education", "academic"):
        if key in sections:
            education = _extract_education(sections[key])
            break

    # Certifications
    certifications: list[str] = []
    for key in ("certifications", "certification", "licenses", "license"):
        if key in sections:
            certifications = _extract_certifications(sections[key])
            break

    result: dict[str, str | None | list[str] | list[dict[str, str | None]]] = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "location": None,  # Location extraction deferred to LLM-enhanced parser
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "education": education,
        "certifications": certifications,
    }

    log.info(
        "resume_parse_completed",
        filename=filename,
        skills_count=len(skills),
        experience_count=len(experience),
        education_count=len(education),
        certifications_count=len(certifications),
    )

    return result
