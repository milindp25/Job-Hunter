# ATS Compliance Checker — Design Spec

Sub-project 5 of 8. Enterprise-grade ATS compliance checking with format validation, keyword optimization, and AI-powered content analysis.

## Scope

**Format compliance** (will an ATS parse this resume?) + **keyword optimization** (will it rank well against a specific job?), delivered as a full diagnostic report with categorized findings, severity levels, and before/after rewrite suggestions.

### Triggers

- **Auto on upload:** Format checks (rules 1–16) run synchronously when a resume is uploaded (~50ms, zero API cost). Results stored immediately.
- **On-demand per job:** Full check (format + keywords + content + suggestions) triggered explicitly by the user for a specific resume + job combo. Uses 1 Gemini API call (~6K tokens).

### What this is NOT

This checker does not simulate a specific ATS product. Real ATS systems vary — Taleo ranks by keyword %, Greenhouse does not auto-rank, Lever presents parsed profiles to recruiters. Our checker provides actionable diagnostics based on common ATS parsing behavior, with transparent messaging about system variability.

---

## Data Model

### AtsCheck (new table)

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users |
| resume_id | UUID | FK → resumes, ondelete CASCADE |
| job_id | UUID \| None | FK → jobs, ondelete CASCADE. Null for format-only checks |
| check_type | str | "format_only" \| "full" |
| prompt_version | str | "v1" — tracks Gemini prompt version for staleness |
| resume_updated_at | datetime | Snapshot of resume.updated_at at check time |
| overall_score | int | 0–100, weighted composite |
| format_score | int | 0–100 |
| keyword_score | int \| None | Null if format-only |
| content_score | int \| None | Null if format-only |
| findings | JSON | list[Finding] — see schema below |
| suggestions | JSON | list[Suggestion] — see schema below |
| ai_analysis_available | bool | False if Gemini failed/skipped/not requested |
| created_at | datetime | UTC |
| updated_at | datetime | UTC |

**Constraints:**
- Unique: (resume_id, job_id) — latest check replaces previous for same combo. Note: PostgreSQL treats NULL != NULL in unique constraints, so format-only checks (job_id=NULL) won't be enforced by the DB constraint alone. Application-level upsert logic (query by resume_id WHERE job_id IS NULL) handles this.
- Index: (user_id, created_at DESC) — for paginated listing
- Cascade deletes on resume_id and job_id FKs

### Finding schema (JSON element)

```json
{
  "id": "uuid-string",
  "category": "format | keyword | content",
  "severity": "critical | warning | info",
  "confidence": "high | medium | low",
  "rule_id": "parseable_text | missing_keyword | vague_language | ...",
  "title": "Human-readable title",
  "detail": "Detailed explanation",
  "suggestion": "What to do about it",
  "section": "experience | skills | summary | null",
  "metadata": { "keyword": "Kubernetes", "job_mentions": 3 },
  "dismissed": false
}
```

Machine-readable `rule_id` + `metadata` enables sub-project 7 (Resume Tailor) to programmatically consume findings and auto-fix them.

### Suggestion schema (JSON element)

```json
{
  "section": "experience | skills | summary",
  "before": "Original text from resume",
  "after": "Suggested replacement",
  "reason": "Why this is better",
  "estimated_impact": "string (e.g., '+15 pts')"
}
```

### UserProfile addition

Add `ai_analysis_consented: bool = False` to UserProfile model. Requires Alembic migration.

---

## Score Calculation

### Weights (full check)

```
overall = format_score × 0.3 + keyword_score × 0.4 + content_score × 0.3
```

### Critical issue caps

| Condition | Overall cap |
|---|---|
| Blocker finding (unparseable text, no extractable content) | 15 |
| Standard critical finding (tables, multi-column, text boxes) | 30 |
| No critical findings | No cap |

The cap overrides the weighted calculation: `overall = min(cap, weighted_calc)`.

### Format score deductions

Start at 100, deduct per finding:
- Blocker (severity "blocker"): −70
- Critical (severity "critical"): −25 each
- Warning: −8 each
- Info: −3 each
- Floor at 0

### Score scenarios

| Scenario | Format | Keywords | Content | Weighted | After Cap |
|---|---|---|---|---|---|
| Great resume, perfect match | 95 | 90 | 85 | 90 | 90 |
| Good format, wrong job | 90 | 20 | 40 | 47 | 47 |
| Has tables (critical), good content | 75 | 85 | 80 | 70.5 | **30** |
| Image-only PDF (blocker) | 30 | 90 | 80 | 61.5 | **15** |
| Perfect format, zero keyword match | 100 | 0 | 50 | 45 | 45 |

**UI copy when capped:** "Overall score capped due to critical format issues that prevent ATS parsing."

---

## Rule-Based Engine (16 rules)

Zero API cost. Runs in ~50ms. Auto-triggered on resume upload.

**Short-circuit behavior:** If rule #1 (parseable_text) fails — blocker-level — skip text-dependent rules (5–14). Only run structural checks (file_size, embedded_images). Returns fewer but more relevant findings.

### Critical / Blocker

| # | Rule ID | Severity | Confidence | Check |
|---|---------|----------|------------|-------|
| 1 | parseable_text | blocker | high | raw_text < 50 chars relative to file size → image-only PDF |
| 2 | text_quality | critical | high | >20% non-word characters → Canva/InDesign garbled extraction |
| 3 | has_tables | critical | medium | PDF table structure detection via pymupdf |
| 4 | multi_column | critical | medium | Text position analysis for multi-column layout |
| 16 | text_boxes | critical | medium | DOCX text box detection via python-docx |

### Warning

| # | Rule ID | Severity | Confidence | Check |
|---|---------|----------|------------|-------|
| 5 | standard_sections | warning | high | Fuzzy match for Experience, Education, Skills headers |
| 6 | contact_info | warning | high | Email + phone + name present in parsed_data |
| 7 | resume_length | warning | high | Flag if <100 words or >1500 words |
| 9 | header_footer_info | warning | medium | Contact info only in PDF header/footer region |
| 10 | bullet_characters | warning | medium | Non-standard bullets (★, ►, ➤) |
| 11 | date_consistency | warning | medium | Inconsistent date formats in experience section |
| 14 | chronological_order | warning | medium | Experience dates not in reverse-chronological order |
| 15 | embedded_images | warning | high | PDF embedded images (logos, headshots, infographics) |

### Info

| # | Rule ID | Severity | Confidence | Check |
|---|---------|----------|------------|-------|
| 8 | file_size | info | high | Flag if >2MB |
| 12 | font_detection | info | low | Non-standard fonts in PDF |
| 13 | hyperlink_formatting | info | low | Raw URLs vs properly formatted links |

---

## Gemini ATS Analysis

Single well-crafted prompt. One API call per full check (~6K tokens). Temperature 0.1.

### Input

- Resume raw text (first 4000 chars)
- Resume parsed_data (skills, experience, education as structured data)
- Job title, company, description, tags
- Rule-based findings summary (so Gemini skips what rules already caught)

### Output (JSON)

```json
{
  "keyword_analysis": {
    "score": 58,
    "matched_keywords": ["Python", "FastAPI", "PostgreSQL"],
    "missing_keywords": ["Kubernetes", "CI/CD", "Terraform"],
    "findings": [
      {
        "rule_id": "missing_keyword",
        "severity": "warning",
        "title": "Missing keyword: Kubernetes",
        "detail": "Job mentions Kubernetes 3 times...",
        "suggestion": "Add Kubernetes to skills section",
        "section": "skills",
        "metadata": { "keyword": "Kubernetes", "job_mentions": 3 }
      }
    ]
  },
  "content_analysis": {
    "score": 64,
    "findings": [
      {
        "rule_id": "vague_language",
        "severity": "warning",
        "title": "Generic phrasing detected",
        "detail": "'Responsible for managing...'",
        "suggestion": "Use action verbs with quantified results",
        "section": "experience",
        "metadata": { "original_text": "Responsible for managing..." }
      }
    ]
  },
  "suggestions": [
    {
      "section": "experience",
      "before": "Responsible for managing a team of developers",
      "after": "Led 8-person engineering team, delivering 3 product launches with 99.9% uptime",
      "reason": "Action verb + team size + quantified outcome",
      "estimated_impact": "+15 pts"
    }
  ],
  "summary": "Strong technical background but missing cloud/DevOps keywords..."
}
```

### Failure handling

If Gemini call fails (rate limit, outage, no API key):
- `ai_analysis_available = false`
- Format results still returned (they're free and instant)
- Keywords/Content sections show "AI analysis unavailable — try again later"
- No retry loop — user can re-trigger manually

### Caching

- Results cached per (resume_id, job_id) combo
- Stale when: resume.updated_at changes, or prompt_version changes
- UI shows "Results outdated — re-run check" for stale results

---

## API Endpoints

### POST /api/v1/ats/check

Run an ATS check on a resume, optionally against a job.

```
Body: { resume_id: UUID, job_id?: UUID }

- job_id null → format-only check (rules 1–16, instant)
- job_id present → full check (rules + Gemini)
- Upserts on (resume_id, job_id) — replaces previous check
- Returns: AtsCheckResponse (full report)
- Validates resume ownership
- Rate limit: max 10 full checks per hour per user (429 if exceeded)
```

### GET /api/v1/ats/results

List past checks for the authenticated user.

```
Query: page (default 1), page_size (default 10), resume_id? (filter)
Returns: paginated list with is_stale flag per check
```

### GET /api/v1/ats/results/{check_id}

Get full report detail for a specific check.

```
Returns: AtsCheckResponse with all findings, suggestions
Validates user ownership
Includes is_stale computed field
```

### PATCH /api/v1/ats/results/{check_id}/findings/{finding_id}/dismiss

Toggle dismissed state on a specific finding.

```
Body: { dismissed: bool }
Validates user ownership
```

### AI Consent Flow

1. Frontend checks `user_profile.ai_analysis_consented` before showing "Run Full Check"
2. If false → frontend shows consent modal, user accepts, PATCH /api/v1/users/profile sets flag
3. Backend validates consent on full check requests — returns 403 `ats_consent_required` if not consented

---

## Service Layer

### services/ats_checker.py (orchestrator)

```
run_format_check(session, resume) → AtsCheck
  - Calls ats_rules.run_all_rules(resume)
  - Calculates format_score
  - Upserts on (resume_id, job_id=None)
  - Called by resume upload service automatically

run_full_check(session, user, resume, job) → AtsCheck
  - Checks rate limit (10 full/hour)
  - Runs format rules (or reuses existing format check if resume_updated_at matches — i.e., resume hasn't changed since last format check)
  - Validates AI consent
  - Calls gemini.analyze_ats(resume, job, format_findings)
  - Calculates keyword_score, content_score, overall_score with caps
  - Upserts on (resume_id, job_id)
  - Handles Gemini failure: ai_analysis_available=false, returns format-only

get_check_results(session, user_id, page, page_size, resume_id?) → paginated list
get_check_detail(session, user_id, check_id) → AtsCheck with is_stale
dismiss_finding(session, user_id, check_id, finding_id, dismissed) → AtsCheck
cleanup_old_checks(session, resume_id, job_id) → None (keeps latest 3)
```

### services/ats_rules.py (rule engine)

```
run_all_rules(resume) → list[Finding]
  - Short-circuits on blocker: skips text-dependent rules
  - Returns findings with auto-generated UUIDs

Individual functions:
  check_parseable_text(resume) → Finding | None
  check_text_quality(resume) → Finding | None
  check_tables(resume) → Finding | None
  ... (one per rule)

calculate_format_score(findings) → tuple[int, bool, bool]
  - Returns (score, has_blocker, has_critical)
```

### services/gemini.py (extend existing)

```
analyze_ats(resume, job, format_findings) → GeminiAtsResult
  - Single prompt, JSON response
  - Temperature 0.1
  - Retry with exponential backoff (shared with matching engine)
  - Returns structured keyword/content/suggestions
```

### Integration: resume upload

`services/resume.py → upload_resume()` calls `ats_checker.run_format_check()` after successful parse. Synchronous — adds ~50ms.

---

## Exceptions

Add to `exceptions.py`:

| Exception | Status | Code |
|---|---|---|
| AtsCheckNotFoundError | 404 | ATS_CHECK_NOT_FOUND |
| AtsCheckError | 500 | ATS_CHECK_ERROR |
| AtsRateLimitError | 429 | ATS_RATE_LIMIT |
| AtsConsentRequiredError | 403 | ATS_CONSENT_REQUIRED |

---

## Frontend

### File structure

```
frontend/src/
  app/ats/
    page.tsx                      # ATS report page (route: /ats?checkId=xxx)
    ats-report-content.tsx        # 'use client' wrapper
  components/ats/
    ats-score-header.tsx          # Score cards row with SVG circular progress
    ats-findings-section.tsx      # Findings list per category (format/keyword/content)
    ats-suggestion-card.tsx       # Before/after diff card with impact estimate
    ats-consent-modal.tsx         # AI privacy consent dialog
    ats-format-badge.tsx          # Small badge for resume card on profile page
    ats-check-button.tsx          # "Run ATS Check" button with loading state
    ats-keyword-bar.tsx           # Keyword coverage bar chart
    ats-stale-banner.tsx          # "Results outdated" warning
  hooks/
    useAtsCheck.ts                # React Query mutations + queries for ATS API
  lib/types.ts                    # Add AtsCheck, AtsFinding, AtsSuggestion types
```

### Entry points

1. **Profile page resume card** — Shows format score badge (auto-populated after upload). "Full ATS Report" button opens report page.
2. **Job match detail** — "Run ATS Check Against This Job" button triggers full check with primary resume.

### Report page layout

Full-page diagnostic report with:
- **Score header:** Overall (large circle) + Format / Keywords / Content (smaller circles) with color-coded arcs
- **Transparency disclaimer:** ATS system variability notice + privacy link
- **Format section:** Pass/fail findings with confidence badges and dismiss buttons
- **Keywords section:** Keyword coverage bar chart + matched/missing findings
- **Content section:** Quality findings with actionable hints
- **Suggestions section:** Git-diff-style before/after cards with estimated point impact, "Powered by Gemini AI" badge
- **Stale banner:** Conditional — shown when resume modified after check, with "Re-run Check" action

### Progressive loading

Format results render instantly (from cached format check or synchronous rules). Keywords, Content, and Suggestions sections show skeleton loaders while Gemini processes (~3–5s). Sections animate in when API returns.

### Types (add to types.ts)

```typescript
interface AtsCheck {
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
}

interface AtsFinding {
  id: string;
  category: 'format' | 'keyword' | 'content';
  severity: 'critical' | 'warning' | 'info';
  confidence: 'high' | 'medium' | 'low';
  ruleId: string;
  title: string;
  detail: string;
  suggestion: string;
  section: string | null;
  metadata: Record<string, unknown>;
  dismissed: boolean;
}

interface AtsSuggestion {
  section: string;
  before: string;
  after: string;
  reason: string;
  estimatedImpact: string;
}
```

---

## Design Considerations

### 1. Machine-readable findings
Structured `rule_id` + `metadata` on every finding enables sub-project 7 (Resume Tailor) to programmatically consume and auto-fix issues.

### 2. Graceful Gemini degradation
Format results always available. AI sections show fallback state when Gemini fails. Never block the whole report on an API call.

### 3. Synchronous format checks on upload
~50ms overhead. Results ready when user views their resume. No background task infrastructure needed.

### 4. Stale check invalidation
`resume_updated_at` snapshot compared against current `resume.updated_at`. UI shows "Results outdated — re-run check" when stale. Also triggers on `prompt_version` change.

### 5. Gemini rate limit coordination
Add a shared retry-with-exponential-backoff wrapper in `services/gemini.py` (new infrastructure — existing gemini.py has no retry logic). Used by both matching engine and ATS checker. 15 RPM free tier limit.

### 6. Score cap for critical format issues
Blocker findings cap overall at 15, standard critical at 30. If ATS can't read the resume, keyword/content scores are irrelevant.

### 7. Confidence levels + dismiss
Each finding has a confidence level (high/medium/low). Users can dismiss findings they consider not applicable. Dismissed findings don't affect score display.

### 8. ATS variability disclaimer
Transparent messaging: "Results based on common ATS parsing behavior (Taleo, Workday, Greenhouse, iCIMS). Individual systems may vary."

### 9. AI privacy consent
Users must consent before first AI-powered check. `ai_analysis_consented` flag on UserProfile. Frontend-led flow with backend validation (403).

### 10. Duplicate check prevention
Unique constraint on (resume_id, job_id). Upsert logic — new check replaces previous for same combo. Handles race conditions via ON CONFLICT UPDATE.

### 11. Prompt versioning
`prompt_version` stored on AtsCheck. When prompt improves, old results flagged as stale. Re-run on user demand.

### 12. PDF text quality detection
Rule #2 detects garbled text extraction (Canva/InDesign/Figma PDFs) via non-word character ratio analysis.

### 13. Check history cleanup
Keep latest 3 checks per (resume_id, job_id) combo. Auto-delete older on new check creation.

### 14. Progressive loading UX
Format results instant, AI sections load with skeleton states. Sections animate in when ready.

### 15. Test fixtures
Sample PDF/DOCX files with known issues (tables, multi-column, image-only, missing sections) for rule engine testing. Gemini responses mocked in tests.

---

## Alembic Migration

New migration adding:
- `ats_checks` table with all fields, constraints, and indexes
- `ai_analysis_consented` column on `user_profiles` table

---

## Gemini API Budget

Free tier: 15 RPM, 1M tokens/day.

| Operation | Tokens | API Calls |
|---|---|---|
| Format-only check | 0 | 0 |
| Full check | ~6K | 1 |
| Daily capacity | ~160 full checks | — |

Rate limit: 10 full checks/user/hour (enforced via DB count query: `SELECT COUNT(*) FROM ats_checks WHERE user_id=? AND check_type='full' AND created_at > now() - interval '1 hour'`). Shared Gemini budget with matching engine.
