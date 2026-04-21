"""Core data models for careergrep."""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Job(BaseModel):
    """A normalized job posting from any ATS source."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: Literal["greenhouse", "lever", "ashby", "workable", "themuse", "arbeitnow"]
    external_id: str
    company: str
    title: str
    url: str
    location: str | None = None
    remote: bool | None = None
    posted_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.now)
    description: str  # full HTML or markdown
    description_text: str  # plain text for keyword matching

    # Scoring — populated later in the pipeline
    keyword_score: int = 0
    claude_score: int | None = None
    claude_reasoning: str | None = None
    claude_red_flags: list[str] = Field(default_factory=list)

    # User state — populated via the UI or API
    status: Literal["new", "seen", "applied", "rejected", "not_interested"] = "new"
    notes: str | None = None

    def is_us_job(self) -> bool:
        """Classify job as US/Remote vs international.

        Watch list sources (Greenhouse, Ashby, etc.) are all US companies — always US.
        Arbeitnow is a European aggregator, so default to international unless the
        location explicitly mentions the US.
        """
        if self.source != "arbeitnow":
            return True

        if not self.location:
            return False  # arbeitnow jobs without location are typically EU

        loc = self.location.lower()
        us_indicators = {"united states", "usa", "u.s.a", "remote, us", "remote us"}
        return any(indicator in loc for indicator in us_indicators)
