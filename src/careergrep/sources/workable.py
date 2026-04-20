"""Workable ATS job source."""

from datetime import datetime

import httpx

from careergrep.models import Job

API_URL = "https://apply.workable.com/api/v3/accounts/{slug}/jobs"

# Workable's public list API doesn't include job descriptions — there's no
# public per-job detail endpoint either. Keyword matching will be title-only
# for Workable jobs. If description matters, consider scraping the HTML page
# (check ToS first) or upgrading to a Workable partner API.
_EMPTY_BODY = {
    "query": "",
    "location": [],
    "department": [],
    "worktype": [],
    "remote": [],
}


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _format_location(loc: dict) -> str | None:
    """Build a readable location string from Workable's location object."""
    parts = [loc.get("city"), loc.get("region"), loc.get("country")]
    return ", ".join(p for p in parts if p) or None


async def fetch_jobs(company_slug: str) -> list[Job]:
    """Fetch all published jobs from a Workable account."""
    url = API_URL.format(slug=company_slug)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=_EMPTY_BODY, timeout=30.0)
        response.raise_for_status()

    data = response.json()
    jobs: list[Job] = []

    for raw in data.get("results", []):
        if raw.get("state") != "published" or raw.get("isInternal"):
            continue

        published_str = raw.get("published", "")
        if not published_str:
            continue

        location = _format_location(raw.get("location", {}))
        job_url = f"https://apply.workable.com/{company_slug}/j/{raw['shortcode']}/"

        job = Job(
            source="workable",
            external_id=str(raw["id"]),
            company=company_slug,
            title=raw.get("title", ""),
            url=job_url,
            location=location,
            remote=raw.get("remote", False) or raw.get("workplace") == "remote",
            posted_at=_parse_datetime(published_str),
            description="",  # not available via public API
            description_text="",
        )
        jobs.append(job)

    return jobs
