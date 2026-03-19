# ATS Compliance Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an enterprise-grade ATS compliance checker that auto-runs format checks on resume upload and provides on-demand keyword/content analysis against specific jobs via Gemini AI.

**Architecture:** Two-layer engine — 16 rule-based format checks (free, ~50ms) + 1 Gemini API call for keyword/content/suggestions (~6K tokens). Results stored in `ats_checks` table with machine-readable findings for future Resume Tailor integration. Frontend shows full diagnostic report with SVG score circles, categorized findings, and before/after suggestion diffs.

**Tech Stack:** FastAPI, SQLModel, PostgreSQL (Neon), Gemini 2.0 Flash, Next.js 16, TypeScript, Tailwind CSS, React Query

**Spec:** `docs/superpowers/specs/2026-03-19-ats-compliance-checker-design.md`

---

## File Structure

### Backend — New Files
| File | Responsibility |
|------|---------------|
| `backend/app/models/ats_check.py` | AtsCheck SQLModel table definition |
| `backend/app/schemas/ats.py` | Pydantic request/response schemas for ATS endpoints |
| `backend/app/services/ats_rules.py` | 16 rule-based format checks (deterministic, zero API cost) |
| `backend/app/services/ats_checker.py` | Orchestrator — coordinates rules + Gemini + scoring + DB |
| `backend/app/routers/ats.py` | HTTP endpoints: POST /check, GET /results, PATCH /dismiss |
| `backend/alembic/versions/XXXX_add_ats_checks_table.py` | Migration: ats_checks table + ai_analysis_consented column |
| `backend/tests/test_ats_rules.py` | Unit tests for rule engine (no DB needed) |
| `backend/tests/test_ats.py` | Integration tests for ATS service + API endpoints |

### Backend — Modified Files
| File | Change |
|------|--------|
| `backend/app/models/__init__.py` | Add `AtsCheck` import |
| `backend/app/models/user.py` | Add `ai_analysis_consented` field to UserProfile |
| `backend/app/exceptions.py` | Add 4 ATS exception classes |
| `backend/app/services/gemini.py` | Add `analyze_ats()` function + retry wrapper |
| `backend/app/services/resume.py` | Hook `run_format_check()` into `upload_resume()` |
| `backend/app/main.py` | Register ATS router |

### Frontend — New Files
| File | Responsibility |
|------|---------------|
| `frontend/src/app/ats/page.tsx` | ATS report page (server component with metadata) |
| `frontend/src/app/ats/ats-report-content.tsx` | 'use client' wrapper for report page |
| `frontend/src/components/ats/ats-score-header.tsx` | Score cards with SVG circular progress rings |
| `frontend/src/components/ats/ats-findings-section.tsx` | Categorized findings list (format/keyword/content) |
| `frontend/src/components/ats/ats-suggestion-card.tsx` | Before/after diff card with impact estimate |
| `frontend/src/components/ats/ats-consent-modal.tsx` | AI privacy consent dialog |
| `frontend/src/components/ats/ats-format-badge.tsx` | Compact format score badge for resume card |
| `frontend/src/components/ats/ats-check-button.tsx` | "Run ATS Check" button with loading state |
| `frontend/src/components/ats/ats-keyword-bar.tsx` | Keyword coverage bar chart |
| `frontend/src/components/ats/ats-stale-banner.tsx` | "Results outdated" warning banner |
| `frontend/src/hooks/useAtsCheck.ts` | React Query hooks for ATS API |

### Frontend — Modified Files
| File | Change |
|------|--------|
| `frontend/src/lib/types.ts` | Add AtsCheck, AtsFinding, AtsSuggestion types |
| `frontend/src/components/profile/resume-card.tsx` | Add format score badge + "ATS Report" button |
| `frontend/src/components/jobs/job-detail-modal.tsx` | Add "Run ATS Check" button |
| `frontend/src/components/layout/header.tsx` | Add "ATS" nav link |

---

## Task 1: Model, Exceptions, and Migration

**Files:**
- Create: `backend/app/models/ats_check.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/exceptions.py`
- Create: `backend/alembic/versions/XXXX_add_ats_checks_table.py`

- [ ] **Step 1: Create AtsCheck model**

Create `backend/app/models/ats_check.py` following existing model patterns (see `models/job_match.py`):

```python
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


class AtsCheck(SQLModel, table=True):
    """ATS compliance check result for a resume, optionally against a job."""

    __tablename__ = "ats_checks"
    __table_args__ = (
        UniqueConstraint("resume_id", "job_id", name="uq_ats_check_resume_job"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    resume_id: uuid.UUID = Field(foreign_key="resumes.id", index=True)
    job_id: uuid.UUID | None = Field(default=None, foreign_key="jobs.id", index=True)

    check_type: str = Field(max_length=20)  # "format_only" | "full"
    prompt_version: str = Field(default="v1", max_length=10)
    resume_updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    overall_score: int = Field(default=0)
    format_score: int = Field(default=0)
    keyword_score: int | None = Field(default=None)
    content_score: int | None = Field(default=None)

    findings: list[dict[str, object]] = Field(
        default_factory=list,
        sa_column=Column(JSON, default=[]),
    )
    suggestions: list[dict[str, object]] = Field(
        default_factory=list,
        sa_column=Column(JSON, default=[]),
    )

    ai_analysis_available: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

- [ ] **Step 2: Add AtsCheck to models __init__**

In `backend/app/models/__init__.py`, add:

```python
from app.models.ats_check import AtsCheck  # noqa: F401
```

- [ ] **Step 3: Add ai_analysis_consented to UserProfile**

In `backend/app/models/user.py`, add to the `UserProfile` class:

```python
ai_analysis_consented: bool = Field(default=False)
```

- [ ] **Step 4: Add ATS exceptions**

In `backend/app/exceptions.py`, add these classes after the existing ones:

```python
class AtsCheckNotFoundError(AppException):
    """Raised when an ATS check result is not found."""

    def __init__(
        self,
        detail: str = "ATS check result not found.",
    ) -> None:
        super().__init__(detail=detail, error_code="ATS_CHECK_NOT_FOUND", status_code=404)


class AtsCheckError(AppException):
    """Raised when an ATS check fails unexpectedly."""

    def __init__(
        self,
        detail: str = "ATS check failed. Please try again.",
    ) -> None:
        super().__init__(detail=detail, error_code="ATS_CHECK_ERROR", status_code=500)


class AtsRateLimitError(AppException):
    """Raised when user exceeds ATS check rate limit."""

    def __init__(
        self,
        detail: str = "Rate limit exceeded. Maximum 10 full checks per hour.",
    ) -> None:
        super().__init__(detail=detail, error_code="ATS_RATE_LIMIT", status_code=429)


class AtsConsentRequiredError(AppException):
    """Raised when AI analysis is requested without user consent."""

    def __init__(
        self,
        detail: str = "AI analysis requires your consent. Please accept the privacy notice first.",
    ) -> None:
        super().__init__(detail=detail, error_code="ATS_CONSENT_REQUIRED", status_code=403)
```

- [ ] **Step 5: Create Alembic migration**

Run: `cd backend && .venv/Scripts/alembic revision --autogenerate -m "add ats_checks table and ai_analysis_consented"`

Verify the generated migration creates the `ats_checks` table with all columns, foreign keys (CASCADE on resume_id and job_id), unique constraint `uq_ats_check_resume_job`, indexes on user_id/resume_id/job_id, and adds `ai_analysis_consented` column to `user_profiles`.

If autogenerate misses anything, manually add. See spec for exact column types.

- [ ] **Step 6: Commit**

```
git add backend/app/models/ats_check.py backend/app/models/__init__.py backend/app/models/user.py backend/app/exceptions.py backend/alembic/versions/
git commit -m "feat(ats): add AtsCheck model, exceptions, and migration"
```

---

## Task 2: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/ats.py`

- [ ] **Step 1: Create ATS schemas**

Create `backend/app/schemas/ats.py` following existing schema patterns (see `schemas/matching.py`):

```python
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
```

- [ ] **Step 2: Commit**

```
git add backend/app/schemas/ats.py
git commit -m "feat(ats): add Pydantic request/response schemas"
```

---

## Task 3: Rule Engine — Core Format Checks

The rule engine is deterministic, zero API cost, runs in ~50ms. This is the core of the format compliance checker.

**Files:**
- Create: `backend/app/services/ats_rules.py`
- Create: `backend/tests/test_ats_rules.py`

- [ ] **Step 1: Write failing tests for the rule engine**

Create `backend/tests/test_ats_rules.py` with test classes:

- `TestParseableText` — tests for normal resume (pass), empty text (blocker), very short text relative to file size (blocker)
- `TestTextQuality` — clean text (pass), garbled non-word characters >20% (critical)
- `TestContactInfo` — complete info (pass), missing email (warning), missing phone (warning)
- `TestStandardSections` — standard headers present (pass), missing Experience section (warning)
- `TestResumeLength` — normal length (pass), <100 words (warning), >1500 words (warning)
- `TestBulletCharacters` — standard bullets (pass), fancy bullets like `►★➤` (warning)
- `TestFileSize` — normal size (pass), >2MB (info)
- `TestFormatScore` — perfect score with no findings, blocker deduction (-70), critical deduction (-25), warning deduction (-8), info deduction (-3), floor at 0
- `TestRunAllRules` — returns list of findings with IDs, short-circuits on blocker (skips text-dependent rules)

Use a `_make_resume()` helper that returns a mock object with `raw_text`, `file_size`, `file_type`, `parsed_data`, `id`, `updated_at` attributes.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_ats_rules.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.ats_rules'`

- [ ] **Step 3: Implement the rule engine**

Create `backend/app/services/ats_rules.py` with:

- `from __future__ import annotations` first
- A helper function `_make_finding(rule_id, severity, confidence, title, detail, suggestion, section, metadata)` that returns a dict with auto-generated UUID `id` field
- 16 individual rule functions, each returning `dict | None`:
  - `check_parseable_text(resume)` — len(raw_text.strip()) < 50 and file_size > 10000 → blocker
  - `check_text_quality(resume)` — regex count non-word chars, ratio > 0.20 → critical
  - `check_tables(resume)` — scan raw_text for tab-heavy patterns (3+ tabs per line) → critical, medium confidence
  - `check_multi_column(resume)` — detect large mid-line whitespace gaps (5+ spaces) → critical, medium confidence
  - `check_text_boxes(resume)` — check file_type == "docx", note limitation → critical, medium confidence
  - `check_standard_sections(resume)` — regex for Experience, Education, Skills headers → warning
  - `check_contact_info(resume)` — check parsed_data for full_name, email, phone → warning
  - `check_resume_length(resume)` — word count <100 or >1500 → warning
  - `check_file_size(resume)` — >2MB → info
  - `check_header_footer_info(resume)` — contact info only in first/last 2 lines → warning, medium
  - `check_bullet_characters(resume)` — regex for `[►★➤➜➡▶◆◇■□▪▸‣⁃]` → warning
  - `check_date_consistency(resume)` — extract date formats, flag if mixed → warning
  - `check_chronological_order(resume)` — extract years from experience, check descending → warning
  - `check_embedded_images(resume)` — file_size/len(raw_text) ratio unusually high → warning
  - `check_font_detection(resume)` — PDF-only, low confidence → info
  - `check_hyperlink_formatting(resume)` — raw URLs detected → info

- `run_all_rules(resume) -> list[dict]`:
  - Run parseable_text first; if blocker, short-circuit (skip text-dependent rules 5-14)
  - Always run structural checks (file_size, embedded_images, text_boxes)
  - Return all findings

- `calculate_format_score(findings) -> tuple[int, bool, bool]`:
  - Start at 100
  - Blocker: -70, Critical: -25, Warning: -8, Info: -3
  - Floor at 0
  - Return (score, has_blocker, has_critical)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_ats_rules.py -v`

Expected: ALL PASS

- [ ] **Step 5: Lint**

Run: `cd backend && .venv/Scripts/ruff check app/services/ats_rules.py tests/test_ats_rules.py --fix`

- [ ] **Step 6: Commit**

```
git add backend/app/services/ats_rules.py backend/tests/test_ats_rules.py
git commit -m "feat(ats): implement 16-rule format compliance engine with tests"
```

---

## Task 4: Gemini ATS Analysis

Extend existing `services/gemini.py` with ATS-specific analysis and a shared retry wrapper.

**Files:**
- Modify: `backend/app/services/gemini.py`

- [ ] **Step 1: Add GeminiAtsResult dataclass**

Add after existing `GeminiMatchResult` dataclass:

```python
@dataclass
class GeminiAtsResult:
    """Parsed result from Gemini ATS compliance analysis."""

    keyword_score: int = 0
    content_score: int = 0
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    keyword_findings: list[dict[str, object]] = field(default_factory=list)
    content_findings: list[dict[str, object]] = field(default_factory=list)
    suggestions: list[dict[str, str]] = field(default_factory=list)
    summary: str = ""
```

- [ ] **Step 2: Add retry wrapper**

Add `_call_gemini_with_retry(model, prompt, max_retries=3)` function that:
- Uses `asyncio.to_thread()` for the sync Gemini SDK call
- Catches rate limit errors (429 or "rate" in error message)
- Retries with exponential backoff: `wait = 2 ** (attempt + 1)` seconds
- Raises `GeminiAnalysisError` after all retries exhausted

- [ ] **Step 3: Add _build_ats_prompt function**

Build a prompt that:
- Receives resume text (first 4000 chars), parsed_data, job details, format findings summary
- Instructs Gemini to NOT repeat format findings already caught
- Requests JSON response with keyword_analysis (score, matched, missing, findings), content_analysis (score, findings), suggestions (max 3, with before/after/reason/estimated_impact), and summary
- Sets specific rules: deduct per missing keyword, flag vague language, spell out acronyms

See spec section "Gemini ATS Analysis" for exact output JSON format.

- [ ] **Step 4: Add analyze_ats function**

```python
async def analyze_ats(
    resume_text: str,
    parsed_data: dict[str, object],
    job_title: str,
    job_company: str,
    job_description: str,
    job_tags: list[str],
    format_findings_summary: str,
) -> GeminiAtsResult:
```

Follows existing `analyze_job_match` pattern:
- Check GEMINI_API_KEY is configured
- Configure genai, build prompt, call with retry wrapper
- Parse JSON response into `GeminiAtsResult`
- Clamp scores to 0-100
- Limit suggestions to 3
- Catch and re-raise as `GeminiAnalysisError`

- [ ] **Step 5: Lint and verify**

Run: `cd backend && .venv/Scripts/ruff check app/services/gemini.py --fix`

- [ ] **Step 6: Commit**

```
git add backend/app/services/gemini.py
git commit -m "feat(ats): add Gemini ATS analysis with retry wrapper"
```

---

## Task 5: ATS Checker Service (Orchestrator)

The central service coordinating rules, Gemini, scoring, and DB operations.

**Files:**
- Create: `backend/app/services/ats_checker.py`

- [ ] **Step 1: Create the ATS checker service**

Create `backend/app/services/ats_checker.py` following existing service patterns (see `services/matching.py`):

**Constants:**
- `RATE_LIMIT_FULL_CHECKS_PER_HOUR = 10`
- `MAX_CHECKS_PER_COMBO = 3`
- `PROMPT_VERSION = "v1"`

**Public functions:**
- `run_format_check(session, resume) -> AtsCheck` — runs rules, calculates format_score with caps, upserts (query by resume_id WHERE job_id IS NULL for format-only), called by resume upload
- `run_full_check(session, user_id, resume_id, job_id) -> AtsCheck` — checks rate limit, checks AI consent, fetches resume+job, reuses format results if fresh, calls Gemini (handles failure gracefully with ai_analysis_available=False), combines all findings with UUIDs, calculates weighted overall with caps, upserts on resume_id+job_id
- `get_check_results(session, user_id, page, page_size, resume_id?) -> tuple[list, int]` — paginated list
- `get_check_detail(session, user_id, check_id) -> AtsCheck` — single check with ownership validation
- `dismiss_finding(session, user_id, check_id, finding_id, dismissed) -> AtsCheck` — toggle dismissed in findings JSON
- `is_check_stale(session, check) -> bool` — compare resume_updated_at and prompt_version

**Private helpers:**
- `_check_rate_limit(session, user_uuid)` — count full checks in last hour, raise AtsRateLimitError if >= 10
- `_check_ai_consent(session, user_uuid)` — verify profile.ai_analysis_consented, raise AtsConsentRequiredError
- `_get_resume(session, user_uuid, resume_uuid)` — fetch with ownership check
- `_get_format_results(session, resume)` — reuse cached format check if resume_updated_at matches, otherwise run fresh
- `_cleanup_old_checks(session, resume_uuid, job_uuid)` — keep latest 3 per combo

**Key patterns:**
- Use `session.flush()` not commit
- Use `structlog.get_logger()` for logging
- Use `uuid.UUID(user_id)` for string-to-UUID conversion
- Use `select()` from sqlmodel for queries
- Handle `job_id IS NULL` with `.is_(None)` for format-only queries

- [ ] **Step 2: Lint**

Run: `cd backend && .venv/Scripts/ruff check app/services/ats_checker.py --fix`

- [ ] **Step 3: Commit**

```
git add backend/app/services/ats_checker.py
git commit -m "feat(ats): implement ATS checker orchestrator service"
```

---

## Task 6: ATS Router (API Endpoints)

**Files:**
- Create: `backend/app/routers/ats.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create ATS router**

Create `backend/app/routers/ats.py` following existing router patterns (see `routers/matching.py`):

**Helper function:**
- `_check_response(check, is_stale) -> AtsCheckResponse` — converts AtsCheck model to response schema, iterates findings/suggestions into response types

**Endpoints:**
- `POST /api/v1/ats/check` — accepts `AtsCheckRequest`, calls `run_full_check` if job_id provided, `run_format_check` otherwise
- `GET /api/v1/ats/results` — paginated list with Query params: page, page_size, resume_id
- `GET /api/v1/ats/results/{check_id}` — single check detail
- `PATCH /api/v1/ats/results/{check_id}/findings/{finding_id}/dismiss` — toggle dismissed state

All endpoints require `Depends(get_current_user)` and `Depends(get_db)`.

- [ ] **Step 2: Register router in main.py**

In `backend/app/main.py`:
- Add: `from app.routers import ats as ats_router`
- Add: `app.include_router(ats_router.router)`

- [ ] **Step 3: Lint**

Run: `cd backend && .venv/Scripts/ruff check app/routers/ats.py app/main.py --fix`

- [ ] **Step 4: Commit**

```
git add backend/app/routers/ats.py backend/app/main.py
git commit -m "feat(ats): add ATS API endpoints and register router"
```

---

## Task 7: Resume Upload Integration

Hook format checks into the resume upload flow.

**Files:**
- Modify: `backend/app/services/resume.py`

- [ ] **Step 1: Add format check call to upload_resume**

In `backend/app/services/resume.py`:
- Add import: `from app.services import ats_checker`
- After the resume is created and flushed (after `await session.flush()`), add a try/except block that calls `await ats_checker.run_format_check(session, resume)`
- Wrap in try/except to never fail the upload if format check fails — log warning and continue

- [ ] **Step 2: Commit**

```
git add backend/app/services/resume.py
git commit -m "feat(ats): auto-run format check on resume upload"
```

---

## Task 8: Integration Tests

**Files:**
- Create: `backend/tests/test_ats.py`

- [ ] **Step 1: Write integration tests**

Create `backend/tests/test_ats.py` with fixtures and test classes:

**Fixtures:**
- `test_resume` — creates a Resume with good raw_text and parsed_data (all sections present, contact info complete)
- `test_job` — creates a Job with description mentioning Kubernetes, CI/CD, Terraform (keywords the test resume is missing)

**Test classes:**
- `TestAtsFormatCheck`:
  - `test_format_check_success` — POST /check with resume_id only, verify 200, check_type="format_only", format_score > 0, keyword_score is None
  - `test_format_check_unauthorized` — POST /check without auth, verify 401

- `TestAtsResults`:
  - `test_list_results_empty` — GET /results with no checks, verify empty list
  - `test_list_results_after_check` — run a check first, then GET /results, verify total=1
  - `test_get_result_detail` — run a check, GET /results/{id}, verify correct data
  - `test_get_result_not_found` — GET /results/{random_uuid}, verify 404

- `TestAtsDismiss`:
  - `test_dismiss_finding` — run a check, dismiss first finding, verify dismissed=True in response

- `TestAtsFullCheck`:
  - `test_full_check_requires_consent` — POST /check with job_id, verify 403 ATS_CONSENT_REQUIRED

- [ ] **Step 2: Run tests**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_ats.py -v`

Expected: ALL PASS

- [ ] **Step 3: Run full test suite**

Run: `cd backend && .venv/Scripts/python -m pytest tests/ -v`

Expected: ALL PASS (no regressions)

- [ ] **Step 4: Commit**

```
git add backend/tests/test_ats.py
git commit -m "test(ats): add integration tests for ATS endpoints"
```

---

## Task 9: Frontend Types and API Hook

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Create: `frontend/src/hooks/useAtsCheck.ts`

- [ ] **Step 1: Add TypeScript types**

In `frontend/src/lib/types.ts`, add at the end:

```typescript
// -- ATS Compliance Checker --

export interface AtsFinding {
  id: string;
  category: 'format' | 'keyword' | 'content';
  severity: 'blocker' | 'critical' | 'warning' | 'info';
  confidence: 'high' | 'medium' | 'low';
  ruleId: string;
  title: string;
  detail: string;
  suggestion: string;
  section: string | null;
  metadata: Record<string, string | number | boolean | null>;
  dismissed: boolean;
}

export interface AtsSuggestion {
  section: string;
  before: string;
  after: string;
  reason: string;
  estimatedImpact: string;
}

export interface AtsCheck {
  id: string;
  resumeId: string;
  jobId: string | null;
  checkType: 'format_only' | 'full';
  overallScore: number;
  formatScore: number;
  keywordScore: number | null;
  contentScore: number | null;
  findings: AtsFinding[];
  suggestions: AtsSuggestion[];
  aiAnalysisAvailable: boolean;
  isStale: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AtsCheckListResponse {
  checks: AtsCheck[];
  total: number;
  page: number;
  pageSize: number;
}
```

- [ ] **Step 2: Create useAtsCheck hook**

Create `frontend/src/hooks/useAtsCheck.ts` with four hooks:
- `useAtsCheck(checkId)` — query single check by ID
- `useAtsResults(resumeId?)` — query paginated results, optional resume filter
- `useRunAtsCheck()` — mutation to POST /check, invalidates queries on success
- `useDismissFinding()` — mutation to PATCH dismiss, updates cache optimistically

Use `@tanstack/react-query` and `apiClient` from `@/lib/api-client`.

- [ ] **Step 3: Commit**

```
git add frontend/src/lib/types.ts frontend/src/hooks/useAtsCheck.ts
git commit -m "feat(ats): add frontend TypeScript types and React Query hooks"
```

---

## Task 10: Frontend Components

Build all ATS UI components following the enterprise design from the v3 mockup.

**Design reference:** `.superpowers/brainstorm/2295-1773901755/frontend-layout-v3.html`

**Files:**
- Create: All files in `frontend/src/components/ats/`

- [ ] **Step 1: Create ats-score-header.tsx**

Score cards with SVG circular progress rings:
- Large circle (80x80) for overall score
- Smaller circles (64x64) for format, keywords, content sub-scores
- Color coding: green (>=80), amber (50-79), red/purple (<50)
- Score formula shown under overall card
- Category detail text (e.g., "5 missing", "3 issues")
- Props: `overallScore`, `formatScore`, `keywordScore`, `contentScore`

- [ ] **Step 2: Create ats-findings-section.tsx**

Categorized findings list:
- Props: `category`, `title`, `icon`, `score`, `findings[]`, `onDismiss`
- Each finding shows: status icon (pass/warn/fail), text with bold highlights, confidence badge, dismiss button
- Hint text with actionable suggestion on separate line
- Category icon with colored background (green for format, amber for keyword, purple for content)

- [ ] **Step 3: Create ats-suggestion-card.tsx**

Before/after diff card:
- Props: single `AtsSuggestion`
- Section label + estimated impact badge ("+ N pts")
- Git-diff-style: red before with strikethrough, green after
- Diff markers (-/+) in colored badges
- Reason with lightbulb icon
- Left gradient border accent (blue to purple)

- [ ] **Step 4: Create ats-consent-modal.tsx**

AI privacy consent dialog:
- Uses Radix AlertDialog (or equivalent)
- Explains what data goes to Gemini
- "Accept" calls PATCH /users/profile to set ai_analysis_consented
- "Decline" closes modal
- Props: `open`, `onOpenChange`, `onConsented`

- [ ] **Step 5: Create utility components**

- `ats-format-badge.tsx` — Compact badge showing format score with color coding. Used in resume card.
- `ats-check-button.tsx` — "Run ATS Check" button with loading spinner during mutation. Props: `resumeId`, `jobId?`, `onSuccess`
- `ats-keyword-bar.tsx` — Horizontal bar chart: green (matched), amber (preferred missing), dark (required missing). Props: `matched`, `preferredMissing`, `requiredMissing`, `total`
- `ats-stale-banner.tsx` — Warning banner: "Results may be outdated — your resume was modified after this check." With "Re-run Check" button. Props: `isStale`, `onRerun`

- [ ] **Step 6: Commit**

```
git add frontend/src/components/ats/
git commit -m "feat(ats): add ATS report UI components"
```

---

## Task 11: ATS Report Page

**Files:**
- Create: `frontend/src/app/ats/page.tsx`
- Create: `frontend/src/app/ats/ats-report-content.tsx`

- [ ] **Step 1: Create page.tsx (server component)**

```typescript
import type { Metadata } from 'next';
import { AtsReportContent } from './ats-report-content';

export const metadata: Metadata = {
  title: 'ATS Compliance Report | Job Hunter',
  description: 'Detailed ATS compliance analysis for your resume',
};

export default function AtsReportPage() {
  return <AtsReportContent />;
}
```

- [ ] **Step 2: Create ats-report-content.tsx (client component)**

`'use client'` wrapper that:
- Reads `checkId` from `useSearchParams()`
- Uses `useAtsCheck(checkId)` to fetch data
- Renders inside `AuthGuard`:
  - Score header (overall + sub-scores)
  - Transparency disclaimer ("Results based on common ATS parsing behavior...")
  - Format findings section
  - Keyword findings section (with keyword bar chart)
  - Content findings section
  - Suggestions section (with "Powered by Gemini AI" badge)
  - Stale banner (conditional, when `isStale` is true)
- Loading state: skeleton loaders for AI sections while format shows instantly
- Error/empty state: "Check not found" with link back to profile

- [ ] **Step 3: Commit**

```
git add frontend/src/app/ats/
git commit -m "feat(ats): add ATS report page with progressive loading"
```

---

## Task 12: Integration with Existing Pages

Connect ATS features to profile resume card and job detail modal.

**Files:**
- Modify: `frontend/src/components/profile/resume-card.tsx`
- Modify: `frontend/src/components/jobs/job-detail-modal.tsx`
- Modify: `frontend/src/components/layout/header.tsx`

- [ ] **Step 1: Add format badge to resume card**

In `frontend/src/components/profile/resume-card.tsx`:
- Import `AtsFormatBadge` and `useAtsResults`
- Fetch ATS results for this resume: `useAtsResults(resume.id)`
- Show format score badge next to filename
- Add "ATS Report" button to actions row linking to `/ats?checkId=<id>`

- [ ] **Step 2: Add ATS check button to job detail modal**

In `frontend/src/components/jobs/job-detail-modal.tsx`:
- Import `AtsCheckButton`
- Add below match score section: "Run ATS Check Against This Job"
- On success, navigate to `/ats?checkId=<result.id>`

- [ ] **Step 3: Add ATS nav link**

In `frontend/src/components/layout/header.tsx`:
- Add "ATS" nav link in the navigation, pointing to `/ats`

- [ ] **Step 4: Build and lint**

Run: `cd frontend && npm run build && npx eslint src/ --max-warnings 0`

Expected: Build succeeds, no lint errors

- [ ] **Step 5: Commit**

```
git add frontend/src/components/profile/resume-card.tsx frontend/src/components/jobs/job-detail-modal.tsx frontend/src/components/layout/header.tsx
git commit -m "feat(ats): integrate ATS checks into profile and job detail views"
```

---

## Task 13: Final Verification

- [ ] **Step 1: Run full backend test suite**

Run: `cd backend && .venv/Scripts/python -m pytest tests/ -v`

Expected: ALL PASS

- [ ] **Step 2: Run backend linting**

Run: `cd backend && .venv/Scripts/ruff check app/ tests/ --fix`

Expected: No errors

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`

Expected: Build succeeds

- [ ] **Step 4: Run frontend lint**

Run: `cd frontend && npx eslint src/ --max-warnings 0`

Expected: No warnings

- [ ] **Step 5: Update CLAUDE.md**

Update the build order section to mark sub-project 5 as DONE:

```
5. **ATS Compliance Checker** (DONE) -- enterprise-grade checks against real ATS systems
```

- [ ] **Step 6: Final commit**

```
git add -A
git commit -m "feat: implement ATS Compliance Checker (sub-project 5/8)"
```
