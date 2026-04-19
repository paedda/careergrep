"""Pipeline: fetch → filter → score → deliver."""

from datetime import datetime, timedelta, timezone

from jobs_radar.config import Settings
from jobs_radar.models import Job
from jobs_radar.scoring.keyword import score_job
from jobs_radar.sources import greenhouse


async def fetch_greenhouse(settings: Settings) -> list[Job]:
    """Fetch jobs from all configured Greenhouse companies."""
    all_jobs: list[Job] = []
    for slug in settings.companies.greenhouse:
        try:
            jobs = await greenhouse.fetch_jobs(slug)
            all_jobs.extend(jobs)
            print(f"  [{slug}] fetched {len(jobs)} jobs")
        except Exception as e:
            # One company failing shouldn't break the whole run
            print(f"  [{slug}] error: {e}")
    return all_jobs


def filter_recent(jobs: list[Job], max_age_hours: int) -> list[Job]:
    """Keep only jobs posted within the last max_age_hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    recent = []
    for job in jobs:
        # Ensure we compare timezone-aware datetimes
        posted = job.posted_at
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        if posted >= cutoff:
            recent.append(job)
    return recent


def score_and_filter(jobs: list[Job], settings: Settings) -> list[Job]:
    """Score jobs by keywords and filter out excluded/low-scoring ones."""
    scored = [score_job(job, settings.keywords) for job in jobs]
    # Drop excluded jobs (score == -1) and below-threshold jobs
    return [j for j in scored if j.keyword_score >= settings.filters.min_score]


async def run(settings: Settings) -> list[Job]:
    """Run the full pipeline: fetch → filter by age → score → filter by score."""
    print("Fetching jobs from Greenhouse...")
    jobs = await fetch_greenhouse(settings)
    print(f"Total fetched: {len(jobs)}")

    recent = filter_recent(jobs, settings.filters.max_age_hours)
    print(f"Posted in last {settings.filters.max_age_hours}h: {len(recent)}")

    results = score_and_filter(recent, settings)
    print(f"After keyword scoring (min score {settings.filters.min_score}): {len(results)}")

    # Sort by score descending
    results.sort(key=lambda j: j.keyword_score, reverse=True)
    return results
