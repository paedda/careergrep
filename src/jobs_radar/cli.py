"""CLI entry points for jobs-radar.

Uses argparse from the standard library — no need for Click or Typer yet.
In PHP you'd use Symfony Console; argparse is Python's built-in equivalent.
"""

import argparse
import asyncio
import sys

from jobs_radar.config import load_settings
from jobs_radar.delivery.email import send_digest
from jobs_radar.pipeline import mark_jobs_seen, run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jobs-radar",
        description="Surface fresh tech job postings and score them against your profile.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch, score, and deliver jobs")
    fetch_parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email delivery, just print results",
    )
    fetch_parser.add_argument(
        "--max-age",
        type=int,
        default=None,
        help="Override max age in hours (default: from config)",
    )
    fetch_parser.add_argument(
        "--no-mark-seen",
        action="store_true",
        help="Don't mark jobs as seen after delivery (useful for testing)",
    )

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
            return

        print(f"\nTop results:")
        for job in jobs[:10]:
            print(f"  [{job.keyword_score:2d}] {job.title} @ {job.company}")
            print(f"       {job.url}")

        if not args.no_email:
            print()
            send_digest(jobs, settings)

        # Mark as seen so we don't re-send in the next run
        if not args.no_mark_seen:
            mark_jobs_seen([j.id for j in jobs])
            print(f"Marked {len(jobs)} job(s) as seen.")


if __name__ == "__main__":
    main()
