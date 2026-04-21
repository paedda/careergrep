"""RemoteOK job source — US-remote tech jobs, no auth required.

Searches by tag so we only fetch PHP/Symfony roles. Full HTML descriptions
included in the API response. RemoteOK asks for a descriptive User-Agent.
"""

from datetime import datetime, timezone

import httpx

from careergrep.models import Job
from careergrep.sources.greenhouse import _strip_html

API_URL = "https://remoteok.com/api"

# Tags to query — each is a separate API call; results are deduped by job id.
TAGS = ["php", "symfony"]


def _parse_datetime(value: str) -> datetime:
    """RemoteOK returns ISO 8601 with timezone offset."""
    return datetime.fromisoformat(value).astimezone(timezone.utc).replace(tzinfo=timezone.utc)


async def fetch_jobs() -> list[Job]:
    """Fetch PHP/Symfony remote jobs from RemoteOK.

    The API returns up to ~25 jobs per tag. First element in each response
    is a metadata object (has a 'legal' key) — we skip non-job entries.
    """
    all_jobs: list[Job] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(headers={"User-Agent": "careergrep/0.1 job-search-tool"}) as client:
        for tag in TAGS:
            try:
                response = await client.get(API_URL, params={"tag": tag}, timeout=30.0)
                response.raise_for_status()
            except Exception as e:
                print(f"  [remoteok/{tag}] error: {e}")
                continue

            data = response.json()

            for raw in data:
                # Skip metadata entry (first item) and any non-job objects
                if not isinstance(raw, dict) or "position" not in raw:
                    continue

                job_id = str(raw["id"])
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                pub_date = raw.get("date", "")
                if not pub_date:
                    continue

                description_html = raw.get("description", "")
                location = raw.get("location") or None

                job = Job(
                    source="remoteok",
                    external_id=job_id,
                    company=raw.get("company", "Unknown"),
                    title=raw.get("position", ""),
                    url=raw.get("url", ""),
                    location=location,
                    remote=True,  # RemoteOK is remote-only by definition
                    posted_at=_parse_datetime(pub_date),
                    description=description_html,
                    description_text=_strip_html(description_html),
                )
                all_jobs.append(job)

    return all_jobs
