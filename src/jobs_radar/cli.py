"""CLI entry points for jobs-radar.

Uses argparse from the standard library — no need for Click or Typer yet.
In PHP you'd use Symfony Console; argparse is Python's built-in equivalent.
"""

import argparse
import asyncio
import sys

from jobs_radar.config import load_settings
from jobs_radar.db import get_connection, init_db
from jobs_radar.delivery.email import send_digest
from jobs_radar.models import Job
from jobs_radar.pipeline import mark_jobs_seen, run


def _print_job(job: Job, verbose: bool = False) -> None:
    """Print a single job to stdout."""
    remote_tag = " [remote]" if job.remote else ""
    location = f" | {job.location}" if job.location else ""
    print(f"  [{job.keyword_score:2d}] {job.title} @ {job.company}{remote_tag}")
    if verbose:
        print(f"       Posted: {job.posted_at.strftime('%Y-%m-%d')} via {job.source}{location}")
        if job.description_text:
            snippet = job.description_text[:160].replace("\n", " ")
            print(f"       {snippet}...")
    print(f"       {job.url}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jobs-radar",
        description="Surface fresh tech job postings and score them against your profile.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch new jobs, score, and deliver")
    fetch_parser.add_argument("--no-email", action="store_true", help="Skip email, print results to terminal")
    fetch_parser.add_argument("--verbose", "-v", action="store_true", help="Show location, date, and description snippet")
    fetch_parser.add_argument("--max-age", type=int, default=None, help="Override max age in hours (default: from config)")
    fetch_parser.add_argument("--no-mark-seen", action="store_true", help="Don't mark jobs as seen (useful for testing)")
    fetch_parser.add_argument("--limit", type=int, default=10, help="Max results to print (default: 10)")

    # list command — browse what's already in the DB
    list_parser = subparsers.add_parser("list", help="List jobs already stored in the DB")
    list_parser.add_argument("--status", default="new", help="Filter by status: new, seen, applied, not_interested (default: new)")
    list_parser.add_argument("--all-statuses", action="store_true", help="Show jobs regardless of status")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Show location, date, and description snippet")
    list_parser.add_argument("--limit", type=int, default=20, help="Max results to show (default: 20)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "fetch":
        settings = load_settings()

        if args.max_age is not None:
            settings.filters.max_age_hours = args.max_age

        jobs = asyncio.run(run(settings))

        if not jobs:
            print("\nNo new matching jobs. Already seen jobs are skipped.")
            print("Tip: use `uv run jobs-radar list` to browse stored jobs, or --max-age to widen the window.")
            return

        print(f"\n{len(jobs)} new job(s) found:")
        for job in jobs[:args.limit]:
            _print_job(job, verbose=args.verbose)

        if len(jobs) > args.limit:
            print(f"  ... and {len(jobs) - args.limit} more. Use --limit to see more.\n")

        if not args.no_email:
            send_digest(jobs, settings)

        if not args.no_mark_seen:
            mark_jobs_seen([j.id for j in jobs])
            print(f"Marked {len(jobs)} job(s) as seen.")

    elif args.command == "list":
        conn = get_connection()
        init_db(conn)

        if args.all_statuses:
            where = "1=1"
            params: tuple = ()
        else:
            where = "status = ?"
            params = (args.status,)

        rows = conn.execute(
            f"SELECT * FROM jobs WHERE {where} ORDER BY keyword_score DESC, posted_at DESC LIMIT ?",
            (*params, args.limit),
        ).fetchall()

        if not rows:
            status_label = "any status" if args.all_statuses else f"status='{args.status}'"
            print(f"No jobs found ({status_label}). Run `uv run jobs-radar fetch` first.")
            return

        print(f"\n{len(rows)} job(s) in DB (status={'any' if args.all_statuses else args.status}):\n")
        import json
        from jobs_radar.db import _row_to_job
        for row in rows:
            job = _row_to_job(row)
            _print_job(job, verbose=args.verbose)


if __name__ == "__main__":
    main()
