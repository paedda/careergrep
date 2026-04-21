"""Tests for pipeline filtering logic."""

from datetime import datetime, timedelta, timezone

import pytest

from careergrep.pipeline import filter_recent, score_and_filter
from tests.conftest import make_job, make_settings


# --- filter_recent ---

def test_recent_job_is_kept():
    job = make_job(posted_at=datetime.now(timezone.utc) - timedelta(hours=12))
    result = filter_recent([job], max_age_hours=24)
    assert len(result) == 1


def test_old_job_is_dropped():
    job = make_job(posted_at=datetime.now(timezone.utc) - timedelta(hours=48))
    result = filter_recent([job], max_age_hours=24)
    assert len(result) == 0


def test_job_exactly_at_cutoff_is_kept():
    # Posted exactly at the cutoff boundary should still be included
    job = make_job(posted_at=datetime.now(timezone.utc) - timedelta(hours=24) + timedelta(seconds=1))
    result = filter_recent([job], max_age_hours=24)
    assert len(result) == 1


def test_naive_datetime_treated_as_utc():
    # Jobs with no timezone info should be treated as UTC, not raise an error
    naive = datetime.now() - timedelta(hours=12)
    job = make_job(posted_at=naive)
    result = filter_recent([job], max_age_hours=24)
    assert len(result) == 1


# --- score_and_filter: hard must_have_any requirement ---

def test_php_in_title_passes_hard_filter():
    settings = make_settings()
    job = make_job(title="Senior PHP Developer", description_text="Backend role at a startup.")
    result = score_and_filter([job], settings)
    assert len(result) == 1


def test_no_php_symfony_fails_hard_filter_even_with_high_nice_score():
    settings = make_settings()
    # Loads of nice_to_have hits but no PHP/Symfony anywhere
    job = make_job(
        title="Senior Backend Engineer",
        description_text="AWS, Remote, AI-powered, Senior Staff role.",
    )
    result = score_and_filter([job], settings)
    assert len(result) == 0


def test_php_only_in_description_passes_if_score_meets_threshold():
    settings = make_settings()
    # PHP in desc (+1) + Senior nice (+1) + AWS nice (+1) = 3, meets min_score
    job = make_job(
        title="Backend Engineer",
        description_text="We use PHP, AWS. Senior role, Remote.",
    )
    result = score_and_filter([job], settings)
    assert len(result) == 1


def test_excluded_job_is_removed():
    settings = make_settings()
    job = make_job(title="Junior PHP Developer", description_text="PHP and Symfony.")
    result = score_and_filter([job], settings)
    assert len(result) == 0


def test_multiple_jobs_filtered_correctly():
    settings = make_settings()
    php_job = make_job(external_id="1", title="Senior PHP Engineer", description_text="PHP Symfony AWS.")
    java_job = make_job(external_id="2", title="Java Engineer", description_text="Spring Boot microservices.")
    junior_job = make_job(external_id="3", title="Junior PHP Developer", description_text="PHP required.")

    result = score_and_filter([php_job, java_job, junior_job], settings)
    assert len(result) == 1
    assert result[0].external_id == "1"
