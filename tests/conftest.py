"""Shared test fixtures.

In pytest, fixtures are reusable setup functions — similar to setUp() in
PHPUnit but more flexible: they're injected by name into test functions,
not inherited from a base class.
"""

from datetime import datetime, timezone

import pytest

from careergrep.config import FiltersConfig, KeywordsConfig, Settings, UserConfig, ClaudeConfig, CompaniesConfig, DeliveryConfig, DiscoveryConfig
from careergrep.models import Job


def make_job(**kwargs) -> Job:
    """Build a Job with sensible defaults, overridable via kwargs."""
    defaults = dict(
        source="arbeitnow",
        external_id="test-123",
        company="Acme Corp",
        title="Senior PHP Developer",
        url="https://example.com/job/123",
        location=None,
        remote=True,
        posted_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        description="<p>We use PHP and Symfony.</p>",
        description_text="We use PHP and Symfony.",
    )
    defaults.update(kwargs)
    return Job(**defaults)


def make_settings(**keyword_overrides) -> Settings:
    """Build a minimal Settings object for scoring tests."""
    keywords = KeywordsConfig(
        must_have_any=["PHP", "Symfony"],
        nice_to_have=["Senior", "AWS", "Remote", "AI"],
        exclude=["Junior", "Intern"],
    )
    for key, val in keyword_overrides.items():
        setattr(keywords, key, val)

    return Settings(
        user=UserConfig(name="Paedda", profile_summary="Senior PHP/Symfony backend engineer."),
        keywords=keywords,
        filters=FiltersConfig(min_score=3),
        claude=ClaudeConfig(enabled=False),
        companies=CompaniesConfig(),
        discovery=DiscoveryConfig(),
        delivery=DeliveryConfig(),
    )
