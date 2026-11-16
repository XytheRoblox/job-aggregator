"""Compare today's fetched jobs against the last run to find what's new,
unchanged, edited, or gone — and flag reposts.

Persisted per company at job_agent/data/jobs/{company}.json so each run
only has to diff against yesterday's snapshot, not re-derive history.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from job_agent.jobs import Job

DEFAULT_JOBS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "jobs"
MISSES_BEFORE_CLOSED = 2  # a job must be absent 2 runs in a row before we call it "gone"


@dataclass
class TrackedJob:
    ats: str
    title: str
    location: str | None
    department: str | None
    url: str
    posted_at: str | None
    status: str  # "open" or "closed"
    misses: int
    first_seen_at: str
    last_seen_at: str


@dataclass
class JobChange:
    job: Job
    change: str  # "new", "unchanged", "edited", "gone", or "repost"


def _safe_filename(company: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-") + ".json"


def load_state(company: str, jobs_dir: Path = DEFAULT_JOBS_DIR) -> dict[str, TrackedJob]:
    path = jobs_dir / _safe_filename(company)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return {external_id: TrackedJob(**fields) for external_id, fields in raw.items()}


def save_state(company: str, state: dict[str, TrackedJob], jobs_dir: Path = DEFAULT_JOBS_DIR) -> None:
    path = jobs_dir / _safe_filename(company)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({eid: asdict(t) for eid, t in state.items()}, indent=2))


def _tracked_from(job: Job, *, status: str, misses: int, first_seen_at: str, last_seen_at: str) -> TrackedJob:
    return TrackedJob(
        ats=job.ats,
        title=job.title,
        location=job.location,
        department=job.department,
        url=job.url,
        posted_at=job.posted_at,
        status=status,
        misses=misses,
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
    )


def _fields_match(job: Job, tracked: TrackedJob) -> bool:
    return (job.title, job.location, job.department) == (tracked.title, tracked.location, tracked.department)


def diff_jobs(
    company: str,
    fetched_jobs: list[Job],
    previous_state: dict[str, TrackedJob],
    now: datetime | None = None,
) -> tuple[dict[str, TrackedJob], list[JobChange]]:
    """Compare today's jobs against the previous run's state.

    Returns the updated state (save it with save_state) and the list of
    changes: every job fetched today, plus any previously-open job that
    just crossed the miss threshold and is now considered gone.
    """
    now_str = (now or datetime.now(timezone.utc)).isoformat()
    fetched_by_id = {job.external_id: job for job in fetched_jobs}
    new_state: dict[str, TrackedJob] = dict(previous_state)
    changes: list[JobChange] = []

    # a job reappearing under a new external_id but the same title+location
    # at a company where we'd already marked the old id closed — that's a repost
    closed_lookup = {(t.title, t.location) for t in previous_state.values() if t.status == "closed"}

    for external_id, job in fetched_by_id.items():
        previous = previous_state.get(external_id)

        if previous is None:
            change = "repost" if (job.title, job.location) in closed_lookup else "new"
            new_state[external_id] = _tracked_from(job, status="open", misses=0, first_seen_at=now_str, last_seen_at=now_str)
        elif previous.status == "closed":
            # reappeared under the SAME external_id after being closed — also a repost
            change = "repost"
            new_state[external_id] = _tracked_from(
                job, status="open", misses=0, first_seen_at=previous.first_seen_at, last_seen_at=now_str
            )
        else:
            change = "unchanged" if _fields_match(job, previous) else "edited"
            new_state[external_id] = _tracked_from(
                job, status="open", misses=0, first_seen_at=previous.first_seen_at, last_seen_at=now_str
            )
        changes.append(JobChange(job=job, change=change))

    for external_id, previous in previous_state.items():
        if previous.status != "open" or external_id in fetched_by_id:
            continue

        misses = previous.misses + 1
        if misses < MISSES_BEFORE_CLOSED:
            new_state[external_id] = TrackedJob(**{**asdict(previous), "misses": misses})
            continue  # quietly waiting for a second miss — not reported as a change yet

        new_state[external_id] = TrackedJob(**{**asdict(previous), "misses": misses, "status": "closed"})
        ghost_job = Job(
            external_id=external_id,
            company=company,
            ats=previous.ats,
            title=previous.title,
            location=previous.location,
            department=previous.department,
            url=previous.url,
            posted_at=previous.posted_at,
        )
        changes.append(JobChange(job=ghost_job, change="gone"))

    return new_state, changes
