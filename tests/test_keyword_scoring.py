"""Tests for keyword-based job scoring."""

import pytest

from careergrep.scoring.keyword import score_job
from tests.conftest import make_job, make_settings


@pytest.fixture
def settings():
    return make_settings()


def test_php_in_title_scores_high(settings):
    job = make_job(title="Senior PHP Developer", description_text="Backend role.")
    result = score_job(job, settings.keywords)
    # PHP in title = +3, Senior in nice_to_have = +1
    assert result.keyword_score >= 4


def test_symfony_in_title_scores_high(settings):
    job = make_job(title="Symfony Backend Engineer", description_text="We build APIs.")
    result = score_job(job, settings.keywords)
    assert result.keyword_score >= 3


def test_php_in_description_only_scores_lower(settings):
    job = make_job(title="Backend Engineer", description_text="We use PHP and AWS.")
    result = score_job(job, settings.keywords)
    # PHP in desc = +1, AWS nice_to_have = +1 → score 2 (below min but > 0)
    assert result.keyword_score == 2


def test_no_match_scores_zero(settings):
    job = make_job(title="Java Engineer", description_text="Spring Boot microservices.")
    result = score_job(job, settings.keywords)
    assert result.keyword_score == 0


def test_excluded_term_sets_score_negative(settings):
    job = make_job(title="Junior PHP Developer", description_text="PHP and Symfony required.")
    result = score_job(job, settings.keywords)
    assert result.keyword_score == -1


def test_excluded_term_in_description_also_excluded(settings):
    job = make_job(title="PHP Developer", description_text="Open to interns and junior devs.")
    result = score_job(job, settings.keywords)
    assert result.keyword_score == -1


def test_nice_to_have_adds_to_score(settings):
    job = make_job(
        title="Senior PHP Engineer",
        description_text="PHP, Symfony, AWS, Remote-first team. AI-powered product.",
    )
    result = score_job(job, settings.keywords)
    # PHP in title (+3) + Senior nice (+1) + Symfony desc (+1) + AWS nice (+1) + Remote nice (+1) + AI nice (+1)
    assert result.keyword_score >= 7


def test_must_have_title_hit_not_double_counted_in_desc(settings):
    # PHP appears in both title and description — should only count title bonus (+3), not +3 +1
    job = make_job(title="PHP Developer", description_text="Looking for a PHP expert.")
    result = score_job(job, settings.keywords)
    # PHP title +3; desc hit is already in title_hits so desc_only is empty
    assert result.keyword_score == 3


def test_case_insensitive_matching(settings):
    job = make_job(title="php developer", description_text="symfony framework experience required.")
    result = score_job(job, settings.keywords)
    assert result.keyword_score >= 3


def test_short_exclude_term_uses_word_boundary(settings):
    # "AI" should not match inside "email" or "AIM"
    settings.keywords.exclude = ["AI"]
    job = make_job(title="Email Marketing Engineer", description_text="Send email campaigns.")
    result = score_job(job, settings.keywords)
    assert result.keyword_score != -1  # "AI" in "email" should NOT trigger exclusion
