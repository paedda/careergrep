"""Claude-powered job scoring using the Anthropic SDK.

Runs after keyword filtering — only the jobs that already matched PHP/Symfony
are sent to Claude, so we never waste tokens on irrelevant postings.
"""

import os

import anthropic

from careergrep.config import ClaudeConfig, Settings
from careergrep.models import Job

# Rough token cost estimate for budget guard.
# claude-sonnet-4-6: ~$3/M input, ~$15/M output.
# Each job prompt is ~800 input tokens + ~200 output tokens.
COST_PER_JOB_USD = (800 * 3 + 200 * 15) / 1_000_000  # ≈ $0.006


def _build_prompt(job: Job, settings: Settings) -> str:
    return f"""You are evaluating a job posting for a specific candidate. Score how well it matches their profile.

## Candidate Profile
{settings.user.profile_summary}

## Job Posting
Company: {job.company}
Title: {job.title}
Location: {job.location or "Not specified"} | Remote: {job.remote}
Source: {job.source}

Description:
{job.description_text[:3000]}

## Task
Score this job on a scale of 1–10 for fit with the candidate profile. Consider:
- Tech stack match (PHP/Symfony experience is the candidate's core — is it required or at least present?)
- Seniority level (Senior or Staff — not junior, not management-only)
- Remote-first or fully remote (candidate is in Erie, CO and wants remote)
- Role type (backend engineering, not sales/HR/marketing/PM)
- Company/product interest

Respond in this exact JSON format (no markdown, no extra text):
{{
  "score": <integer 1-10>,
  "reasoning": "<2-3 sentences explaining the score>",
  "red_flags": ["<flag1>", "<flag2>"]
}}

Red flags examples: "requires on-site in NYC", "junior-level despite senior title", "PHP mentioned only as legacy tech being replaced", "sales role not engineering".
Use an empty array if no red flags."""


def score_jobs_with_claude(jobs: list[Job], settings: Settings) -> list[Job]:
    """Score jobs using Claude. Returns jobs with claude_score populated.

    Skips scoring if Claude is disabled or budget would be exceeded.
    Jobs that fail to score (API error, parse error) keep claude_score=None.
    """
    cfg: ClaudeConfig = settings.claude
    if not cfg.enabled:
        return jobs

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("  [claude] ANTHROPIC_API_KEY not set — skipping Claude scoring")
        return jobs

    estimated_cost = len(jobs) * COST_PER_JOB_USD
    if estimated_cost > cfg.daily_budget_usd:
        print(f"  [claude] {len(jobs)} jobs would cost ~${estimated_cost:.3f}, exceeding daily budget ${cfg.daily_budget_usd} — skipping")
        return jobs

    client = anthropic.Anthropic(api_key=api_key)
    print(f"  [claude] scoring {len(jobs)} jobs with {cfg.model}...")

    for job in jobs:
        try:
            response = client.messages.create(
                model=cfg.model,
                max_tokens=300,
                messages=[{"role": "user", "content": _build_prompt(job, settings)}],
            )
            # response.content is a list of content blocks; first is the text block
            raw = response.content[0].text.strip()

            # Parse the JSON response — using stdlib json, not eval
            import json
            data = json.loads(raw)

            job.claude_score = int(data["score"])
            job.claude_reasoning = data.get("reasoning", "")
            job.claude_red_flags = data.get("red_flags", [])

        except Exception as e:
            print(f"  [claude] error scoring {job.title} @ {job.company}: {e}")

    scored = [j for j in jobs if j.claude_score is not None]
    print(f"  [claude] scored {len(scored)}/{len(jobs)} jobs")
    return jobs
