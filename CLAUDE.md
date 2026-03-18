# Job Hunter

AI-powered job matching platform. Public product built with FastAPI + Next.js.

## Architecture

- **Backend**: FastAPI + SQLModel + PostgreSQL (Neon) + Redis (Upstash)
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind CSS
- **Auth**: JWT + OAuth (Google, GitHub, LinkedIn)
- **LLM**: Gemini 2.0 Flash (free tier) — used in sub-project 4+
- **Job Sources**: Official APIs (RemoteOK, The Muse, Adzuna, Indeed, USAJobs) + Apify for LinkedIn (optional)

## Project Structure

```
backend/           # FastAPI application
  app/
    main.py        # App entry, CORS, exception handlers
    config.py      # pydantic-settings (env vars)
    database.py    # Async SQLModel engine + sessions
    models/        # SQLModel table models
    schemas/       # Pydantic request/response schemas
    routers/       # API route handlers (HTTP layer only)
    services/      # Business logic (never import routers)
    utils/         # Security, helpers
    dependencies.py # FastAPI Depends() — auth, DB sessions
    exceptions.py  # Custom exception classes
  alembic/         # Database migrations
  tests/           # pytest-asyncio tests

frontend/          # Next.js 16 application
  src/
    app/           # App Router pages
    components/    # React components (ui/, auth/, layout/, onboarding/, profile/, dashboard/)
    hooks/         # Custom hooks (useAuth, useProfile)
    lib/           # API client, auth tokens, types, utils
```

## Conventions

### Backend
- `from __future__ import annotations` in all Python files
- Full type annotations — no `Any` types
- Layered architecture: routers → services → models. Routers never touch DB directly.
- Services use `session.flush()` not `session.commit()` — the `get_db()` dependency handles commit/rollback
- Custom exceptions in `exceptions.py`, caught by global handler
- Structured logging with `structlog`
- Ruff for linting (`pyproject.toml` has config). B008 ignored for FastAPI Depends() pattern.

### Frontend
- TypeScript strict mode — no `any` types
- `'use client'` only where needed (hooks, state, event handlers)
- All types in `src/lib/types.ts`
- Forms: react-hook-form + zod validation
- State: zustand (auth), @tanstack/react-query (server state)
- UI primitives from @radix-ui, styled with Tailwind
- Named exports (except page.tsx which needs default)

## Commands

```bash
# Backend
cd backend
.venv/Scripts/python -m pytest tests/ -v    # Run tests
.venv/Scripts/ruff check app/               # Lint
.venv/Scripts/ruff check app/ --fix         # Auto-fix lint

# Frontend
cd frontend
npm run build                               # TypeScript check + build
npx eslint src/ --max-warnings 0            # Lint
npm run dev                                 # Dev server on :3000
```

## Build Order (8 sub-projects)

1. **Foundation** (DONE) — scaffolding, auth, profiles, onboarding wizard
2. **Resume Parser & Storage** — upload, parse, store resumes; LinkedIn profile import
3. **Job Aggregation** — connect to job APIs, fetch/store listings
4. **Matching Engine** — NLP + Gemini scoring, rank jobs vs profiles
5. **ATS Compliance Checker** — enterprise-grade checks against real ATS systems
6. **Resume Generator** — LaTeX templates, customization, PDF output
7. **Resume Tailor** — modify resume to match job descriptions
8. **Polish & Launch** — dashboard UX, notifications, deployment

## Environment

- Python 3.13 (use `py -3.13` on Windows)
- Node.js 22
- PostgreSQL via Neon (free tier)
- Redis via Upstash (free tier)
- No Docker needed
