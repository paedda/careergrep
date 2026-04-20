"""Pipeline: fetch → filter → score → persist → deliver."""

import sqlite3
from datetime import datetime, timedelta, timezone

from careergrep.config import Settings
from careergrep.db import get_connection, init_db, mark_seen, save_job
from careergrep.models import Job
from careergrep.scoring.keyword import score_job
from careergrep.sources import arbeitnow, ashby, greenhouse, lever, themuse, workable


async def _fetch_source(source_name: str, fetch_fn, slugs: list[str]) -> list[Job]:
    """Fetch jobs from all company slugs for a given source.

    Errors from individual companies are caught so one bad slug doesn't
    abort the entire run — same pattern you'd use in PHP with try/catch
    inside a foreach.
    """
    all_jobs: list[Job] = []
    for slug in slugs:
        if not slug:
            continue
        try:
            jobs = await fetch_fn(slug)
            all_jobs.extend(jobs)
            print(f"  [{source_name}/{slug}] fetched {len(jobs)} jobs")
        except Exception as e:
            print(f"  [{source_name}/{slug}] error: {e}")
    return all_jobs


async def fetch_all(settings: Settings) -> list[Job]:
    """Fetch jobs from all configured company-slug sources (optional watch list)."""
    all_jobs: list[Job] = []

    sources = [
        ("greenhouse", greenhouse.fetch_jobs, settings.companies.greenhouse),
        ("ashby", ashby.fetch_jobs, settings.companies.ashby),
        ("workable", workable.fetch_jobs, settings.companies.workable),
        ("lever", lever.fetch_jobs, settings.companies.lever),
    ]

    for name, fetch_fn, slugs in sources:
        if not slugs:
            continue
        print(f"Fetching from {name}...")
        jobs = await _fetch_source(name, fetch_fn, slugs)
        all_jobs.extend(jobs)

    return all_jobs


async def fetch_discovery(settings: Settings) -> list[Job]:
    """Fetch jobs via keyword-based discovery sources (no company list needed)."""
    if not settings.discovery.enabled:
        return []

    all_jobs: list[Job] = []

    if "themuse" in settings.discovery.sources:
        print("Fetching from The Muse (Senior/Staff Software Engineers)...")
        try:
            jobs = await themuse.fetch_jobs(
                keywords=settings.keywords.must_have_any,
                max_pages=settings.discovery.max_pages,
            )
            print(f"  [themuse] fetched {len(jobs)} jobs")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"  [themuse] error: {e}")

    if "arbeitnow" in settings.discovery.sources:
        print("Fetching from Arbeitnow (remote jobs)...")
        try:
            jobs = await arbeitnow.fetch_jobs()
            print(f"  [arbeitnow] fetched {len(jobs)} jobs")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"  [arbeitnow] error: {e}")

    return all_jobs


def filter_recent(jobs: list[Job], max_age_hours: int) -> list[Job]:
    """Keep only jobs posted within the last max_age_hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    recent = []
    for job in jobs:
        posted = job.posted_at
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        if posted >= cutoff:
            recent.append(job)
    return recent


def score_and_filter(jobs: list[Job], settings: Settings) -> list[Job]:
    """Score jobs by keywords and filter out excluded/low-scoring ones."""
    scored = [score_job(job, settings.keywords) for job in jobs]
    return [j for j in scored if j.keyword_score >= settings.filters.min_score]


def persist_and_dedup(conn: sqlite3.Connection, jobs: list[Job]) -> list[Job]:
    """Save new jobs to DB; return only the ones we haven't seen before."""
    new_jobs = []
    for job in jobs:
        if save_job(conn, job):
            new_jobs.append(job)
    return new_jobs


async def run(settings: Settings) -> list[Job]:
    """Full pipeline: fetch → filter → score → dedup → persist."""
    conn = get_connection()
    init_db(conn)

    # Fetch from both company watch list and discovery sources
    company_jobs = await fetch_all(settings)
    discovery_jobs = await fetch_discovery(settings)
    all_jobs = company_jobs + discovery_jobs
    print(f"Total fetched: {len(all_jobs)} ({len(company_jobs)} from watch list, {len(discovery_jobs)} from discovery)")

    recent = filter_recent(all_jobs, settings.filters.max_age_hours)
    print(f"Posted in last {settings.filters.max_age_hours}h: {len(recent)}")

    scored = score_and_filter(recent, settings)
    print(f"After keyword scoring (min score {settings.filters.min_score}): {len(scored)}")

    new_jobs = persist_and_dedup(conn, scored)
    print(f"New (not seen before): {len(new_jobs)}")

    new_jobs.sort(key=lambda j: j.keyword_score, reverse=True)
    return new_jobs


def mark_jobs_seen(job_ids: list[str]) -> None:
    """Mark jobs as seen after digest is sent."""
    conn = get_connection()
    mark_seen(conn, job_ids)
