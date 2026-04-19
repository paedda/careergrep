# jobs-radar

A personal job search tool that surfaces genuinely fresh (last 24h) tech job postings from multiple ATS sources, scores them against my profile using Claude, and delivers a daily email digest.

Built as both a practical tool for an active job search and a portfolio project demonstrating Python, FastAPI, TypeScript/React, and AI-native development.

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Pydantic, SQLite, httpx, Anthropic SDK
- **Frontend:** Vite + React + TypeScript + Tailwind CSS
- **Data Sources:** Greenhouse, Lever, Ashby, Workable (public APIs)

## Getting Started

```bash
# Clone the repo
git clone https://github.com/paedda/jobs-radar.git
cd jobs-radar

# Set up Python environment
uv sync

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the pipeline
uv run jobs-radar fetch
```

## Project Status

Under active development. See [PLAN.md](PLAN.md) for the full roadmap.

## Author

**Peter Kallai** - [peterkallai.com](https://peterkallai.com) | [GitHub](https://github.com/paedda)
