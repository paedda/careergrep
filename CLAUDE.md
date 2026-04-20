# careergrep — Claude Code Guide

## Project Overview

A personal job search tool that fetches fresh (last 24h) tech job postings from multiple ATS sources and discovery aggregators, scores them against Peter's profile using keyword matching (and eventually Claude), and delivers a daily email digest. Also serves as a portfolio project demonstrating Python, FastAPI, TypeScript/React, and AI-native development.

**See PLAN.md for the full roadmap and phase breakdown.**

## Developer Profile

**Peter Kallai** — Senior Software Engineer, 18+ years experience.
- Primary stack: PHP/Symfony at scale, MySQL, AWS — coming from a strong backend/infrastructure background
- Learning through this project: Python idioms, FastAPI, TypeScript/React, Anthropic SDK
- **When introducing Python patterns that differ meaningfully from PHP, add a 1–2 line comment explaining the "why".** Don't over-explain obvious things.

## Commands

```bash
# Run the fetch pipeline (no email)
uv run careergrep fetch --no-email

# Run with a wider time window (for testing on weekends)
uv run careergrep fetch --no-email --max-age 720

# Add a dependency
uv add <package>

# Run tests
uv run pytest
```

## Project Structure

```
src/careergrep/
├── cli.py            # CLI entry point (argparse)
├── config.py         # Settings loaded from config.yaml
├── models.py         # Job Pydantic model
├── pipeline.py       # Orchestrates fetch → filter → score
├── db.py             # SQLite persistence + dedup
├── sources/
│   ├── base.py       # JobSource Protocol
│   ├── greenhouse.py # Greenhouse ATS fetcher
│   ├── ashby.py      # Ashby ATS fetcher
│   ├── workable.py   # Workable ATS fetcher
│   ├── lever.py      # Lever ATS fetcher (deprecated API, mostly 404s)
│   ├── arbeitnow.py  # Discovery: remote jobs worldwide (enabled)
│   └── themuse.py    # Discovery: US tech jobs (disabled — stale data)
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
- [x] Phase 2 — Multi-source (Ashby, Workable, Lever, Arbeitnow) + SQLite + dedup + discovery
- [ ] Phase 3 — Claude scoring (Anthropic SDK, structured output)
- [ ] Phase 4 — FastAPI backend + React/TS frontend
- [ ] Phase 5 — Scheduling (launchd) + polish
- [ ] Phase 6 — Deployment (Fly.io / Vercel, optional)

## Tech Stack

- **Python 3.12+** via `uv` (never use pip directly)
- **Pydantic v2** for models and config validation
- **httpx** for async HTTP
- **Jinja2** for email templates
- **SQLite** via plain sqlite3 (no SQLAlchemy)
- **FastAPI** coming in Phase 4

## Coding Standards

- Full type hints on all Python functions
- Keep files under ~200 lines — split when they grow
- Tests for non-trivial logic (sources, scoring); skip glue code
- No premature abstractions — build concrete things first
- Secrets via `.env` only, never in `config.yaml` or committed files
- Use `uv add` for dependencies, never pip

## Configuration

- `config.yaml` — user preferences, keywords, discovery settings, optional company watch list, delivery settings
- `.env` — secrets only (`ANTHROPIC_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`)
- SMTP credentials must be set as env vars for email to work

## Discovery vs Watch List

The tool has two modes of finding jobs:
1. **Discovery** (primary): keyword-based search via aggregators (Arbeitnow). No company list required. Enabled by default.
2. **Watch list** (optional): specific company slugs via their ATS APIs (Greenhouse, Ashby). Good for priority companies you always want to monitor.

## Known Issues / Notes

- Lever v0 public API is deprecated — all slugs return 404. Implemented but disabled in config.
- The Muse free API returns stale (2021) data — implemented but disabled in config.
- Workable public list API has no description field — keyword matching is title-only for those jobs.
- `from` is a Python keyword — in config, it's stored as `from_` internally (mapped in `load_settings()`).
