"""FastAPI application for careergrep.

Exposes the job database over HTTP so the React frontend can read and
update jobs without touching the DB directly.
"""

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from careergrep.log import setup_logging

setup_logging()
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from careergrep import db
from careergrep.models import Job

app = FastAPI(title="careergrep API", version="0.1.0")

# Allow the Vite dev server (and production build) to call this API.
# In production you'd lock this down to your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "PATCH", "POST"],
    allow_headers=["*"],
)


def _get_conn() -> db.sqlite3.Connection:
    """Open a fresh DB connection for each request.

    FastAPI doesn't have a built-in DI container like Symfony's service container,
    so we open/close connections manually per request. Fine for a single-user tool.
    """
    conn = db.get_connection()
    db.init_db(conn)
    return conn


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class JobPatch(BaseModel):
    status: Literal["new", "seen", "applied", "rejected", "not_interested"] | None = None
    notes: str | None = None


class PipelineRunResponse(BaseModel):
    message: str
    jobs_fetched: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/jobs", response_model=list[Job])
def get_jobs(
    status: str | None = Query(None, description="Filter by status"),
    min_score: int = Query(0, description="Minimum keyword score"),
    source: str | None = Query(None, description="Filter by source"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
) -> list[Job]:
    conn = _get_conn()
    return db.list_jobs(conn, status=status, min_score=min_score, source=source, limit=limit, offset=offset)


@app.get("/api/jobs/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    conn = _get_conn()
    job = db.get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.patch("/api/jobs/{job_id}", response_model=Job)
def patch_job(job_id: str, body: JobPatch) -> Job:
    conn = _get_conn()
    job = db.update_job(conn, job_id, status=body.status, notes=body.notes)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline() -> PipelineRunResponse:
    """Trigger a fetch + score pipeline run."""
    from careergrep.config import load_settings
    from careergrep.pipeline import run as _run

    settings = load_settings()
    # pipeline.run is async, so we can await it directly
    jobs = await _run(settings)
    return PipelineRunResponse(message="Pipeline complete", jobs_fetched=len(jobs))
