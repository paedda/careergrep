"""Tests for Job.is_us_job() location classification."""

import pytest

from tests.conftest import make_job


# --- Watch list sources are always US ---

@pytest.mark.parametrize("source", ["greenhouse", "ashby", "workable", "lever", "remoteok"])
def test_watch_list_sources_always_us(source):
    job = make_job(source=source, location="Berlin, Germany")
    assert job.is_us_job() is True


# --- Arbeitnow: default to international ---

def test_arbeitnow_no_location_is_international():
    job = make_job(source="arbeitnow", location=None)
    assert job.is_us_job() is False


def test_arbeitnow_german_city_is_international():
    for location in ["Berlin", "Munich, Bavaria, Germany", "Hamburg", "Cologne"]:
        job = make_job(source="arbeitnow", location=location)
        assert job.is_us_job() is False, f"Expected international for location: {location}"


def test_arbeitnow_explicit_us_is_us():
    job = make_job(source="arbeitnow", location="Remote, US")
    assert job.is_us_job() is True


def test_arbeitnow_united_states_is_us():
    job = make_job(source="arbeitnow", location="San Francisco, United States")
    assert job.is_us_job() is True


def test_arbeitnow_usa_is_us():
    job = make_job(source="arbeitnow", location="New York, USA")
    assert job.is_us_job() is True


def test_arbeitnow_unknown_location_is_international():
    # When we can't confirm US, default to international for Arbeitnow
    job = make_job(source="arbeitnow", location="Remote")
    assert job.is_us_job() is False
