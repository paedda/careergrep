"""Pipeline: fetch → filter → score → persist → deliver."""

import sqlite3
from datetime import datetime, timedelta, timezone

from careergrep.config import Settings
from careergrep.db import get_connection, init_db, mark_seen, save_job
from careergrep.log import get_logger
from careergrep.models import Job
from careergrep.scoring.claude_scorer import score_jobs_with_claude
from careergrep.scoring.keyword import score_job
from careergrep.sources import arbeitnow, ashby, greenhouse, lever, remoteok, themuse, workable

logger = get_logger(__name__)


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
            logger.info("source fetched", extra={"source": source_name, "slug": slug, "count": len(jobs)})
        except Exception as e:
            logger.error("source error", extra={"source": source_name, "slug": slug, "error": str(e)})
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
        logger.info("fetching watch list source", extra={"source": name})
        jobs = await _fetch_source(name, fetch_fn, slugs)
        all_jobs.extend(jobs)

    return all_jobs


async def fetch_discovery(settings: Settings) -> list[Job]:
    """Fetch jobs via keyword-based discovery sources (no company list needed)."""
    if not settings.discovery.enabled:
        return []

    all_jobs: list[Job] = []

    if "themuse" in settings.discovery.sources:
        logger.info("fetching discovery source", extra={"source": "themuse"})
        try:
            jobs = await themuse.fetch_jobs(
                keywords=settings.keywords.must_have_any,
                max_pages=settings.discovery.max_pages,
            )
            logger.info("source fetched", extra={"source": "themuse", "count": len(jobs)})
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error("source error", extra={"source": "themuse", "error": str(e)})

    if "arbeitnow" in settings.discovery.sources:
        logger.info("fetching discovery source", extra={"source": "arbeitnow"})
        try:
            jobs = await arbeitnow.fetch_jobs()
            logger.info("source fetched", extra={"source": "arbeitnow", "count": len(jobs)})
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error("source error", extra={"source": "arbeitnow", "error": str(e)})

    if "remoteok" in settings.discovery.sources:
        logger.info("fetching discovery source", extra={"source": "remoteok"})
        try:
            jobs = await remoteok.fetch_jobs()
            logger.info("source fetched", extra={"source": "remoteok", "count": len(jobs)})
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error("source error", extra={"source": "remoteok", "error": str(e)})

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
    """Score jobs by keywords and filter out excluded/low-scoring ones.

    Two-stage filter:
    1. must_have_any is a hard requirement — at least one term must appear
       anywhere in the job text, regardless of score.
    2. keyword_score must meet min_score threshold.

    This prevents nice_to_have accumulation (AI + AWS + Remote) from passing
    jobs that never mention PHP or Symfony.
    """
    scored = [score_job(job, settings.keywords) for job in jobs]
    result = []
    for j in scored:
        if j.keyword_score < settings.filters.min_score:
            continue
        # Hard check: must_have_any must actually appear somewhere
        searchable = f"{j.title} {j.description_text}".lower()
        if not any(term.lower() in searchable for term in settings.keywords.must_have_any):
            continue
        result.append(j)
    return result


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

    logger.info("pipeline started")

    company_jobs = await fetch_all(settings)
    discovery_jobs = await fetch_discovery(settings)
    all_jobs = company_jobs + discovery_jobs
    logger.info("fetch complete", extra={
        "total": len(all_jobs),
        "watch_list": len(company_jobs),
        "discovery": len(discovery_jobs),
    })

    recent = filter_recent(all_jobs, settings.filters.max_age_hours)
    logger.info("after time filter", extra={"count": len(recent), "max_age_hours": settings.filters.max_age_hours})

    scored = score_and_filter(recent, settings)
    logger.info("after keyword filter", extra={"count": len(scored), "min_score": settings.filters.min_score})

    scored = score_jobs_with_claude(scored, settings)

    new_jobs = persist_and_dedup(conn, scored)
    logger.info("pipeline complete", extra={"new_jobs": len(new_jobs)})

    new_jobs.sort(key=lambda j: (j.claude_score or 0, j.keyword_score), reverse=True)
    return new_jobs


def mark_jobs_seen(job_ids: list[str]) -> None:
    """Mark jobs as seen after digest is sent."""
    conn = get_connection()
    mark_seen(conn, job_ids)
