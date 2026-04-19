"""Base protocol for job sources."""

from typing import Protocol

from jobs_radar.models import Job


class JobSource(Protocol):
    """Protocol that all job sources must implement.

    In PHP you'd use an interface — Python's Protocol is the equivalent,
    but it's structural (duck typing) rather than nominal. A class doesn't
    need to explicitly declare it implements this; it just needs matching methods.
    """

    source_name: str

    async def fetch_jobs(self, company_slug: str) -> list[Job]:
        """Fetch all current jobs for a company."""
        ...
