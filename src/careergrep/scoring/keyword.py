"""Keyword-based job scoring."""

import re

from careergrep.config import KeywordsConfig
from careergrep.models import Job


def _matches_any(text: str, terms: list[str]) -> list[str]:
    """Return which terms appear in text (case-insensitive)."""
    lower = text.lower()
    return [t for t in terms if t.lower() in lower]


def _is_excluded(text: str, exclude_terms: list[str]) -> bool:
    """Check if any exclude terms appear in the title or description.

    Uses word boundary matching for short terms to avoid false positives
    (e.g. 'AI' shouldn't match 'email').
    """
    lower = text.lower()
    for term in exclude_terms:
        term_lower = term.lower()
        # Short terms (<=3 chars) use word boundary matching
        if len(term_lower) <= 3:
            if re.search(rf"\b{re.escape(term_lower)}\b", lower):
                return True
        elif term_lower in lower:
            return True
    return False


def score_job(job: Job, keywords: KeywordsConfig) -> Job:
    """Score a job based on keyword matches.

    Scoring:
    - Each must_have_any match in title: +3
    - Each must_have_any match in description only: +1
    - Each nice_to_have match anywhere: +1
    - Excluded term found: score = -1 (flag to skip)

    Returns the job with keyword_score updated.
    """
    searchable = f"{job.title} {job.description_text}"

    # Check exclusions first
    if _is_excluded(searchable, keywords.exclude):
        job.keyword_score = -1
        return job

    score = 0

    # must_have_any in title is a strong signal
    title_hits = _matches_any(job.title, keywords.must_have_any)
    score += len(title_hits) * 3

    # must_have_any in description (but not already counted from title)
    desc_hits = _matches_any(job.description_text, keywords.must_have_any)
    desc_only = [h for h in desc_hits if h not in title_hits]
    score += len(desc_only)

    # nice_to_have anywhere
    nice_hits = _matches_any(searchable, keywords.nice_to_have)
    score += len(nice_hits)

    job.keyword_score = score
    return job
