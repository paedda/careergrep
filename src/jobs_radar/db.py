"""SQLite persistence layer for jobs-radar.

Uses plain sqlite3 (stdlib) rather than SQLAlchemy — the schema is simple
enough that an ORM adds more complexity than value here.

In PHP you'd typically use PDO or Doctrine. sqlite3 in Python is similar to PDO:
you get a connection, execute parameterized queries, and fetch results.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from jobs_radar.models import Job

# Default DB path: project root
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "jobs.db"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with row_factory set for dict-like access."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    # Row factory lets us access columns by name (like an associative array in PHP)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist yet."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id              TEXT PRIMARY KEY,
            source          TEXT NOT NULL,
            external_id     TEXT NOT NULL,
            company         TEXT NOT NULL,
            title           TEXT NOT NULL,
            url             TEXT NOT NULL,
            location        TEXT,
            remote          INTEGER,
            posted_at       TEXT NOT NULL,
            fetched_at      TEXT NOT NULL,
            description     TEXT,
            description_text TEXT,
            keyword_score   INTEGER DEFAULT 0,
            claude_score    INTEGER,
            claude_reasoning TEXT,
            claude_red_flags TEXT DEFAULT '[]',
            status          TEXT DEFAULT 'new',
            notes           TEXT
        );

        -- Unique constraint on (source, external_id) is how we dedup:
        -- same job fetched twice won't create a second row.
        CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_source_external
            ON jobs (source, external_id);

        CREATE INDEX IF NOT EXISTS idx_jobs_posted_at
            ON jobs (posted_at);

        CREATE INDEX IF NOT EXISTS idx_jobs_status
            ON jobs (status);
    """)
    conn.commit()


def is_seen(conn: sqlite3.Connection, source: str, external_id: str) -> bool:
    """Check if we've already stored this job (by source + external_id)."""
    row = conn.execute(
        "SELECT 1 FROM jobs WHERE source = ? AND external_id = ?",
        (source, external_id),
    ).fetchone()
    return row is not None


def save_job(conn: sqlite3.Connection, job: Job) -> bool:
    """Insert a job. Returns True if inserted, False if it already existed."""
    try:
        conn.execute(
            """
            INSERT INTO jobs (
                id, source, external_id, company, title, url, location, remote,
                posted_at, fetched_at, description, description_text,
                keyword_score, claude_score, claude_reasoning, claude_red_flags,
                status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.id,
                job.source,
                job.external_id,
                job.company,
                job.title,
                job.url,
                job.location,
                int(job.remote) if job.remote is not None else None,
                job.posted_at.isoformat(),
                job.fetched_at.isoformat(),
                job.description,
                job.description_text,
                job.keyword_score,
                job.claude_score,
                job.claude_reasoning,
                json.dumps(job.claude_red_flags),
                job.status,
                job.notes,
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # UNIQUE constraint on (source, external_id) — already exists
        return False


def get_unseen_jobs(
    conn: sqlite3.Connection,
    min_score: int = 0,
    hours: int = 24,
) -> list[Job]:
    """Fetch new jobs (status='new') posted within the last `hours` hours."""
    cutoff = datetime.utcnow().isoformat()
    rows = conn.execute(
        """
        SELECT * FROM jobs
        WHERE status = 'new'
          AND keyword_score >= ?
          AND posted_at >= datetime('now', ? || ' hours')
        ORDER BY keyword_score DESC, posted_at DESC
        """,
        (min_score, f"-{hours}"),
    ).fetchall()
    return [_row_to_job(row) for row in rows]


def mark_seen(conn: sqlite3.Connection, job_ids: list[str]) -> None:
    """Mark jobs as 'seen' after they've been included in a digest."""
    conn.executemany(
        "UPDATE jobs SET status = 'seen' WHERE id = ?",
        [(jid,) for jid in job_ids],
    )
    conn.commit()


def _row_to_job(row: sqlite3.Row) -> Job:
    """Convert a DB row back into a Job model."""
    data = dict(row)
    data["remote"] = bool(data["remote"]) if data["remote"] is not None else None
    data["claude_red_flags"] = json.loads(data["claude_red_flags"] or "[]")
    return Job(**data)
