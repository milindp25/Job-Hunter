from __future__ import annotations

from pydantic import BaseModel


class AtsCheckRequest(BaseModel):
    """Request to run an ATS check."""

    resume_id: str
    job_id: str | None = None


class AtsFindingResponse(BaseModel):
    """Single finding in an ATS check."""

    id: str
    category: str
    severity: str
    confidence: str
    rule_id: str
    title: str
    detail: str
    suggestion: str
    section: str | None
    metadata: dict[str, str | int | float | bool | None]
    dismissed: bool


class AtsSuggestionResponse(BaseModel):
    """AI-generated rewrite suggestion."""

    section: str
    before: str
    after: str
    reason: str
    estimated_impact: str


class AtsCheckResponse(BaseModel):
    """Full ATS check result."""

    id: str
    resume_id: str
    job_id: str | None
    check_type: str
    overall_score: int
    format_score: int
    keyword_score: int | None
    content_score: int | None
    findings: list[AtsFindingResponse]
    suggestions: list[AtsSuggestionResponse]
    ai_analysis_available: bool
    is_stale: bool
    created_at: str
    updated_at: str


class AtsCheckListResponse(BaseModel):
    """Paginated list of ATS checks."""

    checks: list[AtsCheckResponse]
    total: int
    page: int
    page_size: int


class AtsDismissRequest(BaseModel):
    """Request to dismiss/undismiss a finding."""

    dismissed: bool
