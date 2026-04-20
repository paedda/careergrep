"""The Muse job source — keyword-based discovery across US tech companies.

Unlike the ATS sources (Greenhouse, Ashby), this fetches by role/level rather
than by company slug. No API key required for up to 500 requests/hour.
"""

from datetime import datetime

import httpx

from jobs_radar.models import Job
from jobs_radar.sources.greenhouse import _strip_html

API_URL = "https://www.themuse.com/api/public/jobs"

# The Muse uses a fixed category taxonomy. "Software Engineer" is the broadest
# bucket for backend/fullstack roles.
CATEGORY = "Software Engineer"

# Fetch Senior and Staff level roles — skip Mid/Junior/Entry
LEVELS = ["Senior Level", "Staff Level"]


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_location(locations: list[dict]) -> str | None:
    if not locations:
        return None
    return " | ".join(loc["name"] for loc in locations) or None


def _is_remote(locations: list[dict]) -> bool | None:
    for loc in locations:
        if "remote" in loc.get("name", "").lower() or "flexible" in loc.get("name", "").lower():
            return True
    return None


async def fetch_jobs(keywords: list[str], max_pages: int = 5) -> list[Job]:
    """Fetch senior/staff software engineering jobs from The Muse.

    The Muse doesn't support keyword search via the public API — we fetch
    by category + level and let our keyword scorer filter for relevance.
    More pages = more coverage but more API calls (500/hr rate limit).
    """
    jobs: list[Job] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient() as client:
        for level in LEVELS:
            for page in range(max_pages):
                params = {
                    "category": CATEGORY,
                    "level": level,
                    "page": page,
                    "descending": "true",
                }
                try:
                    response = await client.get(API_URL, params=params, timeout=30.0)
                    response.raise_for_status()
                except Exception as e:
                    print(f"  [themuse] page {page} ({level}): {e}")
                    break

                data = response.json()
                results = data.get("results", [])
                if not results:
                    break  # no more pages

                for raw in results:
                    external_id = str(raw["id"])
                    if external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)

                    pub_date = raw.get("publication_date", "")
                    if not pub_date:
                        continue

                    description_html = raw.get("contents", "")
                    location = _parse_location(raw.get("locations", []))

                    job = Job(
                        source="themuse",
                        external_id=external_id,
                        company=raw.get("company", {}).get("name", "Unknown"),
                        title=raw.get("name", ""),
                        url=raw.get("refs", {}).get("landing_page", ""),
                        location=location,
                        remote=_is_remote(raw.get("locations", [])),
                        posted_at=_parse_datetime(pub_date),
                        description=description_html,
                        description_text=_strip_html(description_html),
                    )
                    jobs.append(job)

    return jobs
