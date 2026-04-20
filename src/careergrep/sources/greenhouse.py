"""Greenhouse ATS job source."""

import html
import re
from datetime import datetime

import httpx

from careergrep.models import Job

# Greenhouse returns all jobs at once — no pagination needed for board API
API_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


def _strip_html(text: str) -> str:
    """Convert HTML to plain text for keyword matching."""
    # Unescape HTML entities first (&amp; → &, etc.)
    text = html.unescape(text)
    # Strip tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def _parse_datetime(value: str) -> datetime:
    """Parse Greenhouse datetime string.

    Greenhouse uses ISO 8601 with timezone offset like '2026-01-30T08:57:16-05:00'.
    Python's fromisoformat handles this natively since 3.11.
    """
    return datetime.fromisoformat(value)


def _is_remote(location: str) -> bool | None:
    """Best-effort guess whether a posting is remote."""
    if not location:
        return None
    lower = location.lower()
    if "remote" in lower:
        return True
    return None


async def fetch_jobs(company_slug: str) -> list[Job]:
    """Fetch all current jobs from a Greenhouse board.

    Uses httpx's async client. In PHP you'd use Guzzle with promises —
    httpx + async/await is Python's equivalent, but cleaner.
    """
    url = API_URL.format(slug=company_slug)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

    data = response.json()
    jobs: list[Job] = []

    for raw in data.get("jobs", []):
        location_name = raw.get("location", {}).get("name", "")
        content_html = raw.get("content", "")

        # Greenhouse has 'first_published' for when a job first went live,
        # and 'updated_at' for the last edit. We want first_published as posted_at.
        posted_str = raw.get("first_published") or raw.get("updated_at", "")
        if not posted_str:
            continue  # skip jobs with no date

        job = Job(
            source="greenhouse",
            external_id=str(raw["id"]),
            company=raw.get("company_name", company_slug),
            title=raw.get("title", ""),
            url=raw.get("absolute_url", ""),
            location=location_name or None,
            remote=_is_remote(location_name),
            posted_at=_parse_datetime(posted_str),
            description=content_html,
            description_text=_strip_html(content_html),
        )
        jobs.append(job)

    return jobs
