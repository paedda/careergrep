# jobs-radar — Claude Code Guide

## Project Overview

A personal job search tool that fetches fresh (last 24h) tech job postings from multiple ATS sources, scores them against Peter's profile using Claude, and delivers a daily email digest. Also serves as a portfolio project demonstrating Python, FastAPI, TypeScript/React, and AI-native development.

**See PLAN.md for the full roadmap and phase breakdown.**

## Developer Profile

**Peter Kallai** — Senior Software Engineer, 18+ years experience.
- Primary stack: PHP/Symfony at scale, MySQL, AWS — coming from a strong backend/infrastructure background
- Learning through this project: Python idioms, FastAPI, TypeScript/React, Anthropic SDK
- **When introducing Python patterns that differ meaningfully from PHP, add a 1–2 line comment explaining the "why".** Don't over-explain obvious things.

## Commands

```bash
# Run the fetch pipeline (no email)
uv run jobs-radar fetch --no-email

# Run with a wider time window (for testing on weekends)
uv run jobs-radar fetch --no-email --max-age 720

# Add a dependency
uv add <package>

# Run tests
uv run pytest
```

## Project Structure

```
src/jobs_radar/
├── cli.py            # CLI entry point (argparse)
├── config.py         # Settings loaded from config.yaml
├── models.py         # Job Pydantic model
├── pipeline.py       # Orchestrates fetch → filter → score
├── sources/
│   ├── base.py       # JobSource Protocol
│   └── greenhouse.py # Greenhouse ATS fetcher (async httpx)
├── scoring/
│   └── keyword.py    # Keyword-based scoring
├── delivery/
│   └── email.py      # Jinja2 + Gmail SMTP
└── templates/
    └── digest.html   # HTML email template
```

## Current Phase Status

- [x] Phase 0 — Project setup (uv, Python 3.12, git)
- [x] Phase 1 — Greenhouse fetch + keyword scoring + email digest
- [ ] Phase 2 — Lever, Ashby, Workable sources + SQLite persistence + dedup
- [ ] Phase 3 — Claude scoring (Anthropic SDK, structured output)
- [ ] Phase 4 — FastAPI backend + React/TS frontend
- [ ] Phase 5 — Scheduling (launchd) + polish
- [ ] Phase 6 — Deployment (Fly.io / Vercel, optional)

## Tech Stack

- **Python 3.12+** via `uv` (never use pip directly)
- **Pydantic v2** for models and config validation
- **httpx** for async HTTP
- **Jinja2** for email templates
- **SQLite** coming in Phase 2 (plain sqlite3 or SQLAlchemy)
- **FastAPI** coming in Phase 4

## Coding Standards

- Full type hints on all Python functions
- Keep files under ~200 lines — split when they grow
- Tests for non-trivial logic (sources, scoring); skip glue code
- No premature abstractions — build concrete things first
- Secrets via `.env` only, never in `config.yaml` or committed files
- Use `uv add` for dependencies, never pip

## Configuration

- `config.yaml` — user preferences, keywords, company lists, delivery settings
- `.env` — secrets only (`ANTHROPIC_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`)
- SMTP credentials must be set as env vars for email to work

## Known Issues / Notes

- OpenAI and Notion don't use Greenhouse — slugs returned 404; move to correct sources in Phase 2
- `from` is a Python keyword — in config, it's stored as `from_` internally (mapped in `load_settings()`)
- Greenhouse `first_published` is used as `posted_at`; `updated_at` is a fallback
