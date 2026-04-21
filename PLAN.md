# careergrep — Project Plan

A personal job search tool that surfaces genuinely fresh (last 24h) tech job postings from multiple ATS sources, scores them against my profile using Claude, and delivers a daily email digest.

Built as both a practical tool for an active job search and a portfolio project demonstrating Python, FastAPI, TypeScript/React, and AI-native development.

---

## About the Developer

**Peter Kallai** — Senior Software Engineer, 18+ years of experience.

- **Primary stack:** PHP/Symfony at scale, MySQL, AWS (EC2, ECS, OpenSearch, SQS, etc.), Docker
- **Recent focus:** AI-native features using Claude Code and the Anthropic API in production
- **Learning goals through this project:**
  - Deepen Python skills (coming from strong PHP background)
  - Build hands-on experience with FastAPI and the Anthropic Python SDK
  - Add TypeScript/React to the resume via a small, real frontend
  - Ship an end-to-end full-stack project from scratch
- **GitHub:** `paedda`
- **Site:** peterkallai.com

When writing code, prefer idiomatic Python patterns over literal PHP-style translations, but explain the "why" when there's a meaningful difference (since the developer is most fluent in PHP).

---

## Goals

1. **Primary:** Help me find relevant, recent (last 24h) job postings faster than LinkedIn search allows.
2. **Secondary:** Serve as a portfolio project showing modern full-stack + AI-native work.
3. **Tertiary:** Be something I actually use daily during the job search.

---

## Non-Goals

- Not trying to be a general-purpose job board.
- Not trying to compete with LinkedIn or Indeed.
- Not scraping sites that forbid it in their ToS.
- Not trying to handle 1000s of users — this is a personal tool first, with architecture clean enough to extend if desired.

---

## Tech Stack

**Backend (Python):**
- Python 3.12+
- FastAPI — REST API
- Pydantic — data models & validation
- SQLite — local persistence (simple, zero-ops)
- httpx — async HTTP client
- anthropic — Claude Python SDK
- Jinja2 — HTML email templates
- APScheduler or launchd/cron — daily scheduling
- uv — package and project management (fast, modern)
- pytest — testing

**Frontend (TypeScript):**
- Vite + React + TypeScript
- TanStack Query — server state
- Tailwind CSS — styling
- Minimal component library (shadcn/ui if needed)

**Infrastructure:**
- Local dev first (macOS, Apple Silicon)
- Gmail SMTP for email (App Password)
- Future deployment: Fly.io / Railway for backend, Vercel for frontend, on a subdomain of peterkallai.com or similar.

---

## Data Sources (Phase 1 Targets)

All of these have free, public APIs that do not require authentication for reading public job boards.

| Source | API Endpoint | Notes |
|---|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{company}/jobs` | Many top startups use this |
| Lever | `https://api.lever.co/v0/postings/{company}` | Widely used |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{company}` | Newer but growing |
| Workable | `https://apply.workable.com/api/v3/accounts/{account}/jobs` | Many mid-size companies |

**Note:** Each source operates per-company. The tool will track a configurable list of companies to poll.

**Future sources to consider:** SmartRecruiters, Recruitee, BambooHR, Indeed (requires publisher approval).

---

## Architecture Overview

```
┌───────────────────────────────────────────────────────┐
│ Scheduler (APScheduler / launchd)                     │
│   └─ runs hourly or on-demand                         │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│ Fetcher                                               │
│   ├─ greenhouse_source.py                             │
│   ├─ lever_source.py                                  │
│   ├─ ashby_source.py                                  │
│   └─ workable_source.py                               │
│   Each: async fetch → normalize → Job model           │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│ Storage (SQLite via SQLAlchemy or sqlite3)            │
│   ├─ jobs (id, source, external_id, title, …)         │
│   ├─ companies (name, source, slug)                   │
│   └─ seen_jobs (dedup + "don't notify twice")         │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│ Scoring                                               │
│   ├─ keyword_scorer.py (fast, free)                   │
│   └─ claude_scorer.py (smart, API calls)              │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│ Delivery                                              │
│   ├─ email_digest.py  (Gmail SMTP)                    │
│   └─ web API (FastAPI)                                │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│ Frontend (Vite + React + TS)                          │
│   └─ Browse jobs, mark applied, filter by score       │
└───────────────────────────────────────────────────────┘
```

---

## Repo Structure

```
careergrep/
├── pyproject.toml
├── README.md
├── PLAN.md                    ← this file
├── .env.example
├── .gitignore
├── config.yaml                ← user preferences
│
├── backend/
│   ├── src/
│   │   └── careergrep/
│   │       ├── __init__.py
│   │       ├── main.py              # FastAPI app entry
│   │       ├── config.py            # settings loading
│   │       ├── models.py            # Pydantic models
│   │       ├── db.py                # SQLite setup
│   │       │
│   │       ├── sources/
│   │       │   ├── __init__.py
│   │       │   ├── base.py          # JobSource protocol/ABC
│   │       │   ├── greenhouse.py
│   │       │   ├── lever.py
│   │       │   ├── ashby.py
│   │       │   └── workable.py
│   │       │
│   │       ├── scoring/
│   │       │   ├── keyword.py
│   │       │   └── claude.py
│   │       │
│   │       ├── delivery/
│   │       │   ├── email.py
│   │       │   └── api.py           # FastAPI routes
│   │       │
│   │       ├── pipeline.py          # orchestrates fetch→score→store
│   │       └── cli.py               # command-line entry points
│   │
│   └── tests/
│       ├── test_greenhouse.py
│       ├── test_scoring.py
│       └── …
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   └── client.ts
        ├── components/
        │   ├── JobCard.tsx
        │   ├── JobList.tsx
        │   └── FilterBar.tsx
        ├── hooks/
        │   └── useJobs.ts
        └── types/
            └── job.ts
```

---

## Core Data Model

```python
class Job(BaseModel):
    id: str                    # internal UUID
    source: Literal["greenhouse", "lever", "ashby", "workable"]
    external_id: str           # source's own ID
    company: str
    title: str
    url: str
    location: str | None
    remote: bool | None
    posted_at: datetime
    fetched_at: datetime
    description: str           # full HTML or markdown
    description_text: str      # plain text for keyword matching

    # scoring
    keyword_score: int = 0
    claude_score: int | None = None
    claude_reasoning: str | None = None
    claude_red_flags: list[str] = []

    # user state
    status: Literal["new", "seen", "applied", "rejected", "not_interested"] = "new"
    notes: str | None = None
```

---

## Configuration (`config.yaml`)

```yaml
user:
  name: Peter Kallai
  profile_summary: |
    Senior Software Engineer, 18+ years PHP/Symfony at scale,
    AWS, distributed systems, recent AI-native work with Claude.
    Looking for Senior or Staff Backend roles, remote-first, US-based.

keywords:
  must_have_any:
    - PHP
    - Symfony
    - Senior
    - Staff
    - Backend
  nice_to_have:
    - Claude
    - Anthropic
    - LLM
    - AI
    - AWS
    - Remote
  exclude:
    - Junior
    - Entry level
    - Intern
    - ".NET"

companies:
  greenhouse:
    - anthropic
    - openai
    - stripe
    - figma
    - notion
    # …add freely
  lever:
    - netflix
    - # …
  ashby:
    - arbiter-ai
    - # …
  workable:
    - # …

filters:
  max_age_hours: 24
  min_score: 3

delivery:
  email:
    enabled: true
    to: paedda@paedda.com
    from: paedda@paedda.com
    smtp_host: smtp.gmail.com
    smtp_port: 587
    # smtp_user via env
    # smtp_password (App Password) via env

claude:
  enabled: true
  model: claude-sonnet-4-6   # fast + cheap for scoring
  daily_budget_usd: 2.0
```

Secrets (SMTP password, Anthropic key) via `.env`, never committed.

---

## Phases (Build Order)

### Phase 0 — Project Setup (30 min)
- [x] Initialize repo locally
- [x] Create GitHub repo `paedda/careergrep` (public)
- [x] `uv init` the backend
- [x] Add `README.md`, `PLAN.md`, `.gitignore`, `.env.example`
- [x] First commit + push
- [x] Confirm local Python 3.12+ is working

### Phase 1 — MVP: Fetch + Email (2–3 hours)
**Goal:** End of this phase, running one command produces an email in my inbox with fresh jobs from Greenhouse.

- [x] Define `Job` Pydantic model
- [x] Implement `GreenhouseSource` that fetches jobs for a company slug
- [x] Filter by `posted_at >= now - 24h` and keyword match
- [x] Generate a simple HTML email via Jinja2 template
- [x] Send via Gmail SMTP using App Password
- [x] CLI entry: `uv run careergrep fetch --source greenhouse`

**Key learning outcomes:**
- Python project layout with `uv`
- Pydantic models & validation
- `httpx` for async HTTP
- Working with `datetime` properly (timezones!)
- SMTP email basics

### Phase 2 — Multi-Source + Storage (2–3 hours)
**Goal:** Works across all four ATS sources, persists jobs, doesn't re-notify about the same job.

- [x] Add Lever, Ashby, Workable sources
- [x] Factor out common `JobSource` base class/protocol
- [x] SQLite schema + SQLAlchemy (or plain sqlite3 to keep it simple)
- [x] Dedup: don't alert on jobs we've already seen
- [x] Config file (`config.yaml`) loading with Pydantic settings
- [x] CLI: `uv run careergrep fetch` (all sources, respects config)

**Key learning outcomes:**
- Protocols / abstract base classes in Python
- SQLite basics, data migration patterns
- YAML config + `pydantic-settings`

### Phase 3 — Claude Scoring (1–2 hours)
**Goal:** Each new job gets a 1–10 fit score from Claude with a 1-sentence rationale.

- [x] Anthropic SDK integration
- [x] Prompt design: take user profile + job → structured JSON output (score, reasoning, red_flags)
- [x] Rate limit + budget guard (don't exceed daily_budget_usd)
- [x] Only send top-scoring jobs in email digest
- [x] CLI: `uv run careergrep score`

**Key learning outcomes:**
- Anthropic Python SDK
- Prompt engineering for structured outputs
- Async + concurrent API calls with proper limits

### Phase 4 — FastAPI + React Frontend (4–6 hours)
**Goal:** Browse jobs in a clean UI. Mark as applied. Filter and sort.

**Backend additions:**
- [x] FastAPI app with CORS for local dev
- [x] `GET /api/jobs` with filters (score, source, status, age)
- [x] `PATCH /api/jobs/{id}` for status changes + notes
- [x] `POST /api/pipeline/run` to manually trigger a fetch
- [ ] Basic auth (shared secret via env var — it's only me)

**Frontend:**
- [x] Vite + React + TS + Tailwind setup
- [x] Job list with filters
- [x] Job detail with description, Claude's reasoning, red flags
- [x] Mark as applied / not interested
- [ ] Simple dashboard stats (X new today, Y applied this week)

**Key learning outcomes:**
- FastAPI routes and async handlers
- Vite + React + TypeScript modern frontend setup
- TanStack Query for server state
- Tailwind utility-first styling

### Phase 5 — Scheduling & Polish (1–2 hours)
- [ ] macOS launchd plist to run the pipeline every morning at 7am
- [ ] Logging (JSON structured logs)
- [ ] Error recovery (one source failing doesn't break the rest)
- [ ] Better README with screenshots
- [ ] Config examples

### Phase 6 — Deployment (optional, future)
- [ ] Dockerize backend
- [ ] Deploy backend to Fly.io
- [ ] Deploy frontend to Vercel
- [ ] Wire up a subdomain (e.g. `jobs.peterkallai.com`)
- [ ] Auth hardening (shared secret → proper auth if ever shared)

---

## Coding Standards & Preferences

- **Type everything.** Full type hints on all Python functions; strict TS.
- **Small, focused modules.** If a file gets over ~200 lines, split it.
- **Tests for the non-trivial stuff.** Sources and scoring get tests; glue code doesn't need to.
- **Readable > clever.** This is a learning project — the developer coming back to it in 6 months is me.
- **Document unusual decisions** inline with short comments explaining *why*, not *what*.
- **No premature abstraction.** Three concrete sources before extracting the base class. (Already planned above, but the principle applies everywhere.)

---

## Instructions for Claude Code

When Claude Code picks up work on this project:

1. **Read this file first.** `PLAN.md` is the source of truth for scope and direction.
2. **Check the current phase.** Ask the developer which phase is active if unclear.
3. **Use `uv`** for all Python dependency management — not pip directly.
4. **Write a commit per logical change.** Small, well-described commits.
5. **Teach as you go.** Since this is a learning project, when introducing a Python idiom that differs meaningfully from PHP, add a 1–2 line comment explaining the "why". Don't over-explain trivial things.
6. **Stay within scope.** If a tangent seems interesting, note it in an "Ideas" section at the bottom of this file rather than implementing it.
7. **Ask before adding dependencies.** Prefer the standard library where reasonable.
8. **Prioritize shipping v0.1 end-to-end** over making v0.0 perfect. A working ugly thing beats a half-built beautiful thing.

---

## Ideas (Backlog)

- A "similar jobs" feature — find more jobs like one I marked interesting
- Integration with a local LLM (Ollama on Apple Silicon) as a fallback to Claude API
- Chrome extension that pulls in job postings from LinkedIn directly
- Weekly summary: "Here's what the market looked like this week for senior PHP roles"
- GitHub Action that runs the pipeline on a schedule when deployed

### Multi-user / Public Mode

When opening the tool to other job seekers, these architectural changes are needed:

- **Config → DB**: Move keywords, company lists, and profile summary from `config.yaml` into per-user DB rows
- **Auth**: Add real authentication — OAuth (Google or GitHub login) is the lowest-friction option for a dev-audience tool; replace the Phase 4 shared-secret approach
- **Fetching strategy**: Two options:
  - Per-user company lists (each user picks their own companies to watch)
  - Shared global fetch + per-user scoring (fetch once, score against each user's keyword profile — more efficient at scale)
- **Email delivery**: Replace Gmail SMTP with a transactional email provider (Resend, Postmark, or SendGrid)
- **Scheduling**: Replace launchd with a proper cron/queue on the server side

**Recommendation for Phase 4**: Design the DB schema with a `users` table and FK relationships from the start, but keep the UI single-user for the portfolio. Structurally ready for multi-user without the scope explosion.
