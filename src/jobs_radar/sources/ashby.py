"""Ashby ATS job source."""

from datetime import datetime

import httpx

from jobs_radar.models import Job
from jobs_radar.sources.greenhouse import _strip_html  # reuse the HTML stripper

API_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


async def fetch_jobs(company_slug: str) -> list[Job]:
    """Fetch all current jobs from an Ashby job board.

    Ashby provides both descriptionHtml and descriptionPlain — we use both
    to avoid re-running our own HTML stripper.
    """
    url = API_URL.format(slug=company_slug)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

    data = response.json()
    jobs: list[Job] = []

    for raw in data.get("jobs", []):
        # Skip unlisted jobs (internal-only postings)
        if not raw.get("isListed", True):
            continue

        published_str = raw.get("publishedAt", "")
        if not published_str:
            continue

        description_html = raw.get("descriptionHtml", "")
        # Ashby provides plain text directly — no need to strip HTML ourselves
        description_text = raw.get("descriptionPlain") or _strip_html(description_html)

        job = Job(
            source="ashby",
            external_id=str(raw["id"]),
            company=company_slug,
            title=raw.get("title", ""),
            url=raw.get("jobUrl", ""),
            location=raw.get("location") or None,
            remote=raw.get("isRemote") or raw.get("workplaceType") == "Remote",
            posted_at=_parse_datetime(published_str),
            description=description_html,
            description_text=description_text,
        )
        jobs.append(job)

    return jobs
