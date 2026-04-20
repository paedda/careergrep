"""Arbeitnow job source — remote tech jobs, no auth required.

Aggregates from Greenhouse, SmartRecruiters, and Team Tailor.
Focuses on remote and European positions with English-language postings.
Full job descriptions included in the API response.
"""

from datetime import datetime, timezone

import httpx

from jobs_radar.models import Job
from jobs_radar.sources.greenhouse import _strip_html

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def _parse_datetime(value: int) -> datetime:
    """Arbeitnow uses Unix timestamps (seconds)."""
    return datetime.fromtimestamp(value, tz=timezone.utc)


async def fetch_jobs() -> list[Job]:
    """Fetch remote tech jobs from Arbeitnow.

    Returns up to 100 jobs per page. We fetch page 1 only — the pipeline's
    filter_recent() will drop anything older than max_age_hours anyway.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                API_URL,
                params={"remote": "true"},
                timeout=30.0,
            )
            response.raise_for_status()
        except Exception as e:
            print(f"  [arbeitnow] error: {e}")
            return []

    data = response.json()
    jobs: list[Job] = []

    for raw in data.get("data", []):
        created_at = raw.get("created_at")
        if not created_at:
            continue

        description_html = raw.get("description", "")

        job = Job(
            source="arbeitnow",
            external_id=raw["slug"],
            company=raw.get("company_name", "Unknown"),
            title=raw.get("title", ""),
            url=raw.get("url", ""),
            location=raw.get("location") or None,
            remote=raw.get("remote", True),
            posted_at=_parse_datetime(created_at),
            description=description_html,
            description_text=_strip_html(description_html),
        )
        jobs.append(job)

    return jobs
