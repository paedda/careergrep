"""Lever ATS job source.

NOTE: Lever's v0 public API appears to have been deprecated or restricted as of
early 2026 — all company slugs return 404. The implementation is here for
completeness and future use if access is restored or a new endpoint is found.
"""

from datetime import datetime, timezone

import httpx

from jobs_radar.models import Job
from jobs_radar.sources.greenhouse import _strip_html

API_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


def _parse_datetime(value: int | str) -> datetime:
    """Lever timestamps are Unix milliseconds (int) or ISO strings."""
    if isinstance(value, int):
        # Unix ms → datetime. Python's fromtimestamp takes seconds.
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    return datetime.fromisoformat(value)


async def fetch_jobs(company_slug: str) -> list[Job]:
    """Fetch all current jobs from a Lever job board."""
    url = API_URL.format(slug=company_slug)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

    data = response.json()

    # v0 API returns a list directly (not wrapped in a key)
    if not isinstance(data, list):
        return []

    jobs: list[Job] = []

    for raw in data:
        created_at = raw.get("createdAt")
        if not created_at:
            continue

        description_html = raw.get("descriptionBody", "") or raw.get("description", "")
        location = raw.get("categories", {}).get("location") or raw.get("text", "")

        job = Job(
            source="lever",
            external_id=str(raw["id"]),
            company=company_slug,
            title=raw.get("text", ""),
            url=raw.get("hostedUrl", raw.get("applyUrl", "")),
            location=location or None,
            remote="remote" in (location or "").lower(),
            posted_at=_parse_datetime(created_at),
            description=description_html,
            description_text=_strip_html(description_html),
        )
        jobs.append(job)

    return jobs
