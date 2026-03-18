# Job Hunter — Foundation Sub-project Plan

## Context

Building a public job hunting platform that scrapes jobs from APIs, ranks them against user profiles using AI, checks ATS compliance, and generates tailored LaTeX resumes. This is **Sub-project 1 of 8** — establishing the project foundation: scaffolding, auth, user profiles, and database schema that all subsequent sub-projects build on.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend | FastAPI + SQLModel | Async, auto-docs, SQLModel merges ORM + schemas |
| Frontend | Next.js (App Router) | SSR for SEO, best React DX for public product |
| Database | PostgreSQL (Neon free tier) | Relational + JSONB, best fit for user-job relationships |
| Cache/Queue | Redis (Upstash free tier) | Cache + future Celery broker |
| Auth | JWT + OAuth (Google, GitHub, LinkedIn) | Low-friction signup + LinkedIn profile import |
| ORM | SQLModel (SQLAlchemy under hood) | FastAPI-native, reduces boilerplate |
| LLM | Gemini 2.0 Flash (free tier) | Primary AI engine, $0 cost |
| Job Sources | Official APIs + Apify (optional) | RemoteOK, The Muse, Adzuna, Indeed, USAJobs + LinkedIn via Apify (configurable) |
| Background Tasks | FastAPI BackgroundTasks (upgrade to Celery in sub-project 3) | Simple for now |
| Deployment | Railway (backend) + Vercel (frontend) + Neon (DB) | All free tiers |

## Full Build Order (8 sub-projects)

1. **Foundation** (this plan) — scaffolding, auth (email + Google + GitHub + LinkedIn OAuth), user profiles, onboarding wizard, DB
2. **Resume Parser & Storage** — upload, parse, store resumes; extract skills; LinkedIn profile import (OAuth + URL scrape fallback)
3. **Job Aggregation** — connect to job APIs, fetch/store listings; Apify for LinkedIn jobs (optional)
4. **Matching Engine** — NLP + Gemini scoring, rank jobs vs profiles using comprehensive user profile data
5. **ATS Compliance Checker** — enterprise-grade checks against Workday, Greenhouse, Lever, Taleo, iCIMS parsing rules
6. **Resume Generator** — LaTeX templates, customization, PDF output
7. **Resume Tailor** — modify resume to match job descriptions
8. **Polish & Launch** — dashboard UX, notifications, deployment

---

## Enterprise-Grade Coding Standards

### Backend (Python/FastAPI)
- **Type safety everywhere** — all function signatures fully typed, Pydantic models for all request/response schemas, no `Any` types unless absolutely necessary
- **Layered architecture** — strict separation: routers (HTTP layer) → services (business logic) → repositories (data access). Routers never touch the database directly
- **Dependency injection** — use FastAPI's `Depends()` for database sessions, auth, and all cross-cutting concerns. No global state
- **Error handling** — custom exception classes (`UserNotFoundError`, `DuplicateEmailError`, etc.) with a global exception handler that returns consistent error response format `{detail, error_code, status_code}`
- **Input validation** — Pydantic validators on all incoming data. Sanitize strings, enforce length limits, validate email format
- **Security** — CORS whitelist (not `*`), rate limiting on auth endpoints, bcrypt cost factor ≥12, parameterized queries (SQLModel handles this), HTTPS-only cookies for refresh tokens
- **Logging** — structured JSON logging with `structlog`, correlation IDs for request tracing, log levels (DEBUG/INFO/WARNING/ERROR)
- **Config management** — all secrets via environment variables, never hardcoded. `.env.example` documents every required variable
- **Code formatting** — `ruff` for linting + formatting (replaces black/isort/flake8), enforced via pre-commit hooks
- **Testing** — minimum 80% coverage goal, unit tests for services, integration tests for API endpoints, fixtures for database state
- **API versioning** — all routes under `/api/v1/` for future versioning support
- **Async throughout** — async database sessions via `asyncpg`, async HTTP calls via `httpx`, async service methods

### Frontend (Next.js/React/TypeScript)
- **Strict TypeScript** — `strict: true` in tsconfig, no `any` types, all props/state/API responses typed with interfaces
- **Component architecture** — small, focused components. Container/presentational pattern where appropriate. Max ~150 lines per component file
- **Error boundaries** — React error boundaries for graceful failure handling, user-friendly error states
- **Loading states** — skeleton loaders (not spinners) for content areas, optimistic UI updates where appropriate
- **Form handling** — `react-hook-form` + `zod` for validation. Client-side validation mirrors server-side rules
- **API layer** — centralized API client with interceptors for auth token refresh, error handling, and request/response typing
- **State management** — `zustand` for global state (auth, user profile). React Query / SWR for server state caching
- **Accessibility** — WCAG 2.1 AA compliance: semantic HTML, ARIA labels, keyboard navigation, focus management, color contrast ≥4.5:1
- **Responsive design** — mobile-first, Tailwind breakpoints (sm/md/lg/xl), tested at 320px, 768px, 1024px, 1440px
- **Code quality** — ESLint + Prettier, enforced via pre-commit hooks
- **Performance** — Next.js Image component for images, dynamic imports for heavy components, minimize client-side JS bundle

## UX Design Principles

### Core UX Standards
- **Progressive disclosure** — don't overwhelm users with all options at once. Show what's needed now, reveal complexity gradually
- **Feedback loops** — every user action gets immediate visual feedback (button press states, loading indicators, success/error toasts)
- **Forgiving design** — undo support where possible, confirmation dialogs for destructive actions, auto-save draft state in the onboarding wizard
- **Consistency** — uniform component patterns (buttons, forms, cards), consistent spacing scale (Tailwind's 4px grid), same interaction patterns everywhere
- **Clear hierarchy** — visual weight guides the eye: primary actions prominent, secondary actions subdued, destructive actions clearly marked (red)

### Onboarding Wizard UX
- **Progress indicator** — always-visible step progress bar showing current step, completed steps, and remaining steps
- **Non-linear navigation** — users can jump to any completed step to edit, not forced into sequential order after initial pass
- **Auto-save per step** — wizard saves progress on each step transition, users can leave and return without losing data
- **Smart defaults** — pre-fill from resume/LinkedIn, suggest common skills via autocomplete
- **Validation inline** — show field errors immediately on blur, not just on submit. Use encouraging language ("Almost there!" not "Invalid input")
- **Skip option** — every step except email/name should be skippable, with a gentle nudge to complete later

### Form Design
- **Labels always visible** — no placeholder-only labels (accessibility issue). Floating labels or top-aligned labels
- **Helpful microcopy** — brief hints below fields explaining format or purpose
- **Smart grouping** — related fields grouped visually, logical tab order
- **Error recovery** — clear error messages that explain what went wrong AND how to fix it

### Dashboard & Navigation
- **Clean information hierarchy** — primary content area dominates, navigation doesn't compete for attention
- **Empty states** — friendly, actionable empty states ("No jobs matched yet — complete your profile to get started")
- **Breadcrumbs/context** — user always knows where they are in the app

---

## User Setup Requirements

Before implementation begins, you'll need the following ready. I'll prompt you at the right time, but here's the full list so you can prepare:

**Required (must have before starting):**
- [x] Python 3.13 installed (confirmed)
- [x] Node.js 18+ installed (confirmed)
- [ ] **Neon account** (free PostgreSQL) — sign up at [neon.tech](https://neon.tech), create a project, get the connection string. Put it in `.env` as `DATABASE_URL`
- [ ] **Upstash account** (free Redis) — sign up at [upstash.com](https://upstash.com), create a Redis database, get the URL + token. Put in `.env` as `REDIS_URL`

**Required for OAuth (can be added to `.env` later):**
- [ ] **Google OAuth:** Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials → Create OAuth 2.0 Client ID. Set redirect URI to `http://localhost:8000/api/v1/auth/google/callback`. Get `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET`
- [ ] **GitHub OAuth:** Go to [GitHub Developer Settings](https://github.com/settings/developers) → OAuth Apps → New OAuth App. Set callback URL to `http://localhost:8000/api/v1/auth/github/callback`. Get `GITHUB_CLIENT_ID` + `GITHUB_CLIENT_SECRET`
- [ ] **LinkedIn OAuth:** Go to [LinkedIn Developer Portal](https://developer.linkedin.com/) → Create App → Auth tab → Add redirect URL `http://localhost:8000/api/v1/auth/linkedin/callback`. Get `LINKEDIN_CLIENT_ID` + `LINKEDIN_CLIENT_SECRET`

**Nice to have (can be added later):**
- [ ] Gemini API key (for sub-project 4, not needed yet)
- [ ] Apify API key (for sub-project 3 LinkedIn scraping, optional)

## Parallel Agent Execution Strategy

Use a master agent that dispatches sub-agents in parallel waves. Each wave completes before the next starts. Within a wave, all tasks are independent and run simultaneously.

### Wave 1: Scaffolding (all parallel)
| Agent | Task | Files |
|-------|------|-------|
| Agent A | Backend scaffolding | `backend/app/main.py`, `config.py`, `database.py`, `pyproject.toml` |
| Agent B | Frontend scaffolding | `frontend/` — Next.js init, Tailwind config, layout, API client |
| Agent C | Infrastructure | `.env.example`, root `.gitignore` update, pre-commit config |

### Wave 2: Data Layer + Auth Core (all parallel)
| Agent | Task | Files |
|-------|------|-------|
| Agent D | Database models + Alembic | `models/user.py`, `alembic/`, initial migration |
| Agent E | Auth service + security utils | `services/auth.py`, `utils/security.py`, `dependencies.py` |
| Agent F | Frontend auth components | `components/auth/`, `hooks/useAuth.ts`, `lib/auth.ts` |

### Wave 3: Routes + Pages (all parallel)
| Agent | Task | Files |
|-------|------|-------|
| Agent G | Auth + user API routes | `routers/auth.py`, `routers/users.py`, `schemas/auth.py`, `schemas/user.py` |
| Agent H | Onboarding backend | `services/onboarding.py`, `services/resume_parser.py`, `schemas/onboarding.py` |
| Agent I | Frontend pages | `app/login/`, `app/register/`, `app/dashboard/`, `app/profile/` |

### Wave 4: Onboarding Wizard + Tests (all parallel)
| Agent | Task | Files |
|-------|------|-------|
| Agent J | Onboarding wizard frontend | `app/onboarding/page.tsx`, `components/onboarding/*` |
| Agent K | Landing page | `app/page.tsx` (hero, features, CTA) |
| Agent L | Tests | `tests/conftest.py`, `test_auth.py`, `test_users.py`, `test_onboarding.py` |

### Wave 5: Integration + Polish
| Agent | Task | Files |
|-------|------|-------|
| Agent M | Integration testing + CORS + middleware | End-to-end flow verification |
| Agent N | Code review + linting setup | `ruff` config, `pre-commit`, ESLint, Prettier |

---

## Foundation Implementation Plan

### Step 1: Project Scaffolding

Create the monorepo structure:

```
job-hunter/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, lifespan
│   │   ├── config.py            # pydantic-settings: env vars
│   │   ├── database.py          # SQLModel engine + async session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── user.py          # User + UserProfile models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Login/register request/response
│   │   │   ├── user.py          # Profile update schemas
│   │   │   └── onboarding.py    # Onboarding wizard step schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # /auth/* endpoints
│   │   │   └── users.py         # /users/* endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Auth business logic
│   │   │   ├── user.py          # User/profile business logic
│   │   │   ├── onboarding.py    # Onboarding logic + profile completeness
│   │   │   └── resume_parser.py # Basic resume parsing (PDF/DOCX → structured data)
│   │   ├── dependencies.py      # get_current_user, get_db
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── security.py      # JWT creation/verification, password hashing
│   ├── alembic/                 # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   └── test_users.py
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Landing page
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── onboarding/page.tsx  # Multi-step wizard
│   │   │   ├── dashboard/page.tsx
│   │   │   └── profile/page.tsx
│   │   ├── components/
│   │   │   ├── ui/              # Reusable UI components
│   │   │   ├── auth/            # Auth forms
│   │   │   ├── onboarding/      # Wizard step components
│   │   │   └── layout/          # Header, sidebar, footer
│   │   ├── lib/
│   │   │   ├── api.ts           # Axios/fetch wrapper
│   │   │   ├── auth.ts          # Token management
│   │   │   └── types.ts         # TypeScript interfaces
│   │   └── hooks/
│   │       └── useAuth.ts       # Auth context + hook
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── .env.example                 # All required env vars documented
├── .gitignore
└── README.md
```

**Key dependencies:**

Backend (`pyproject.toml`):
- `fastapi`, `uvicorn[standard]`
- `sqlmodel`, `asyncpg`, `alembic`
- `python-jose[cryptography]` (JWT)
- `passlib[bcrypt]` (password hashing)
- `authlib`, `httpx` (OAuth)
- `pydantic-settings` (config)
- `python-multipart` (file uploads)
- `pymupdf` (PDF parsing) or `pdfplumber`
- `python-docx` (DOCX parsing)
- `structlog` (structured JSON logging)
- `ruff` (linting + formatting)
- `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (testing + coverage)
- `pre-commit` (git hooks for code quality)

Frontend (`package.json`):
- `next`, `react`, `react-dom`, `typescript`
- `tailwindcss`, `@tailwindcss/forms`
- `axios` (API client with interceptors)
- `zustand` (global state: auth, user profile)
- `@tanstack/react-query` (server state caching, auto-refetch)
- `react-hook-form` + `zod` (form handling + validation)
- `sonner` (toast notifications)
- `eslint`, `prettier` (code quality)
- `@radix-ui/react-*` (accessible UI primitives — dialog, dropdown, etc.)

### Step 2: Database Models & Migrations

**User model** (`backend/app/models/user.py`):

```python
class User(SQLModel, table=True):
    id: uuid.UUID (PK, default=uuid4)
    email: str (unique, indexed)
    hashed_password: str | None  # nullable for OAuth users
    full_name: str
    avatar_url: str | None
    auth_provider: str  # "email" | "google" | "github" | "linkedin"
    auth_provider_id: str | None  # OAuth provider's user ID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class UserProfile(SQLModel, table=True):
    id: uuid.UUID (PK)
    user_id: uuid.UUID (FK -> User, unique)
    phone: str | None
    location: str | None
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    years_of_experience: int | None
    desired_roles: list[str]  # JSONB
    desired_locations: list[str]  # JSONB
    min_salary: int | None
    skills: list[dict]  # JSONB - [{name, level, years}]
    education: list[dict]  # JSONB - [{institution, degree, field, start, end}]
    experience: list[dict]  # JSONB - [{company, title, description, start, end}]
    certifications: list[str]  # JSONB
    languages: list[dict]  # JSONB - [{language, proficiency}]
    summary: str | None  # Professional summary / headline
    onboarding_completed: bool = False  # Track if wizard is done
    profile_completeness: int = 0  # Percentage 0-100
```

- Create initial Alembic migration
- Seed script for development data

### Step 3: Auth System

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Email/password signup |
| POST | `/api/v1/auth/login` | Email/password login → JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Invalidate refresh token |
| GET | `/api/v1/auth/google` | Redirect to Google OAuth |
| GET | `/api/v1/auth/google/callback` | Google OAuth callback |
| GET | `/api/v1/auth/github` | Redirect to GitHub OAuth |
| GET | `/api/v1/auth/github/callback` | GitHub OAuth callback |
| GET | `/api/v1/auth/linkedin` | Redirect to LinkedIn OAuth |
| GET | `/api/v1/auth/linkedin/callback` | LinkedIn OAuth callback (also imports profile data) |

**JWT strategy:**
- Access token: 15-minute TTL, stored in memory (frontend)
- Refresh token: 7-day TTL, stored in httpOnly cookie
- Token blacklist via Redis for logout

**OAuth flow:**
1. Frontend opens `/api/v1/auth/google` (or github, or linkedin)
2. Backend redirects to provider's authorization URL
3. User authorizes → redirected to callback URL
4. Backend exchanges code for user info
5. Create or find user by email → issue JWT tokens
6. Redirect to frontend with tokens

**LinkedIn OAuth special behavior:**
- Uses LinkedIn's OpenID Connect (Sign In with LinkedIn v2)
- Requests `openid`, `profile`, `email`, `w_member_social` scopes
- On first login, imports LinkedIn profile data (name, headline, skills, experience, education) into UserProfile
- User can re-sync LinkedIn data later from profile settings

### Step 4: User Profile Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/users/me` | Get current user + profile |
| PUT | `/api/v1/users/me` | Update profile fields |
| PUT | `/api/v1/users/me/skills` | Update skills list |
| PUT | `/api/v1/users/me/experience` | Update work experience |
| PUT | `/api/v1/users/me/education` | Update education |
| POST | `/api/v1/users/me/resume/parse` | Upload resume → parse and return extracted fields (auto-fill) |
| POST | `/api/v1/users/me/linkedin/import` | Import profile from LinkedIn URL (scrape fallback) |
| PUT | `/api/v1/users/me/onboarding` | Save onboarding wizard progress |
| DELETE | `/api/v1/users/me` | Deactivate account (soft delete) |

### Step 5: Onboarding Wizard

Multi-step wizard that runs after first signup. Goal: build a comprehensive user profile.

**Wizard steps:**

1. **Welcome + Resume Upload** (optional)
   - User uploads resume (PDF/DOCX)
   - Backend parses resume → extracts: name, email, phone, skills, experience, education, summary
   - All extracted fields are auto-populated into the wizard form fields
   - User can also connect LinkedIn (OAuth) or paste LinkedIn URL to import data
   - All fields remain editable — auto-fill is a starting point, not final

2. **Personal Info** (pre-filled from resume/LinkedIn if available)
   - Full name, phone, location
   - LinkedIn URL, GitHub URL, portfolio URL
   - Professional summary / headline

3. **Skills & Expertise**
   - Technical skills with proficiency level (beginner/intermediate/advanced/expert)
   - Years of experience per skill
   - Soft skills selection
   - Pre-filled from resume parsing, user can add/remove/adjust levels

4. **Work Experience** (pre-filled from resume if available)
   - Company, title, dates, description
   - Key achievements / impact metrics
   - Add multiple entries, all editable

5. **Education & Certifications** (pre-filled from resume if available)
   - Institution, degree, field of study, dates
   - Certifications and licenses
   - Add multiple entries

6. **Job Preferences**
   - Desired roles (multiple)
   - Desired locations (multiple, including remote)
   - Minimum salary expectation
   - Job type: full-time, part-time, contract, internship
   - Industries of interest

7. **Review & Complete**
   - Show profile completeness percentage
   - Summary of all entered data
   - Option to go back and edit any section
   - Mark onboarding as complete

**Auto-fill behavior:**
- When resume is uploaded at step 1, parse it immediately via backend
- Return extracted fields as structured JSON
- Frontend pre-fills all subsequent wizard steps with extracted data
- Fields show a subtle indicator ("auto-filled from resume") so user knows to review
- LinkedIn import works the same way — merges with any existing data
- If both resume and LinkedIn provide data, prefer LinkedIn for work history (usually more complete) and resume for skills/summary

### Step 6: Frontend Pages

- **Landing page** (`/`) — hero section, feature highlights, CTA to register
- **Login** (`/login`) — email/password form + OAuth buttons (Google, GitHub, LinkedIn)
- **Register** (`/register`) — name, email, password form + OAuth buttons
- **Onboarding** (`/onboarding`) — multi-step wizard (protected, shown after first signup)
- **Dashboard** (`/dashboard`) — protected page, placeholder for future features, displays user name + profile completeness
- **Profile** (`/profile`) — edit profile form with all sections from onboarding (skills, experience, education, etc.)

**Auth flow (frontend):**
- `AuthProvider` context wraps the app
- `useAuth()` hook provides: user, login, logout, isAuthenticated
- Middleware protects `/dashboard`, `/profile`, and `/onboarding` routes
- After first signup → redirect to `/onboarding` wizard
- After completing onboarding → redirect to `/dashboard`
- Returning users who haven't completed onboarding → redirect to `/onboarding`
- Auto-refresh tokens before expiry
- Store access token in memory, refresh token as httpOnly cookie

### Step 7: Cloud Database Setup

No local Docker needed. Use cloud-hosted free tiers:

- **PostgreSQL:** Neon (neon.tech) — free tier, 0.5GB storage, connection pooling built-in
  - User creates project → copies connection string → adds to `.env` as `DATABASE_URL`
  - Format: `postgresql://user:pass@ep-xxx.region.neon.tech/dbname?sslmode=require`
- **Redis:** Upstash (upstash.com) — free tier, 10K commands/day
  - User creates Redis DB → copies URL + token → adds to `.env` as `REDIS_URL`
  - Format: `rediss://default:token@xxx.upstash.io:6379`

### Step 8: Tests

- **Auth tests:** register, login, refresh, logout, duplicate email, OAuth mock (Google, GitHub, LinkedIn)
- **Profile tests:** get profile, update profile, update skills/experience/education, unauthorized access
- **Onboarding tests:** resume upload + parse, LinkedIn URL import, wizard step progression, profile completeness calculation
- Use `pytest-asyncio` + `httpx.AsyncClient` for async testing
- Test database: separate PostgreSQL database or SQLite for speed

---

## Testing Strategy

### After Every Change — Automated Verification

**Backend (run after any backend code changes):**
1. Run `pytest` — all unit and integration tests must pass
2. Run `ruff check` — no linting errors
3. Start uvicorn and hit `/health` endpoint to verify server starts clean

**Frontend (run after any frontend code changes):**
1. Run `npm run build` — TypeScript compilation must succeed with no errors
2. Run `npm run lint` — ESLint passes
3. Start Next.js dev server via `preview_start`
4. Use `preview_screenshot` + `preview_snapshot` to visually verify:
   - Pages render correctly (no blank screens, no layout breaks)
   - Components display as expected
   - Responsive layouts at different viewports (mobile, tablet, desktop via `preview_resize`)
5. Use `preview_click` + `preview_fill` to test interactive flows:
   - Navigation between pages works
   - Forms accept input and show validation
   - Buttons and links respond correctly
6. Check `preview_console_logs` for any JavaScript errors

### End-to-End Verification (after each Wave completes)

**Wave 1 complete:** Backend starts (`/health` returns 200), frontend renders landing page
**Wave 2 complete:** Database tables created, auth service logic works in unit tests
**Wave 3 complete:** Register → login → get profile flow works via API docs (`/docs`)
**Wave 4 complete:** Full onboarding wizard flow tested visually in Chrome:
  - Open Chrome → navigate to app
  - Register new account → verify redirect to onboarding
  - Walk through all 7 wizard steps
  - Upload resume → verify fields auto-populate
  - Edit auto-filled fields → verify changes persist
  - Complete wizard → verify redirect to dashboard
  - Visit profile page → verify all data shows correctly
**Wave 5 complete:** All tests pass, linting clean, full user flow works end-to-end

### Visual Testing Checklist (Chrome)
For each page, verify via screenshot/snapshot:
- [ ] Landing page: hero, features section, CTA buttons visible
- [ ] Login page: email/password form + 3 OAuth buttons (Google, GitHub, LinkedIn)
- [ ] Register page: form fields + OAuth buttons
- [ ] Onboarding wizard: progress bar, step content, navigation buttons
- [ ] Dashboard: user greeting, profile completeness indicator
- [ ] Profile: all sections editable (skills, experience, education, preferences)
- [ ] Mobile responsive: test at 375px width
- [ ] Error states: invalid form inputs show proper error messages
- [ ] Loading states: skeleton loaders appear during data fetches
