from datetime import datetime, timedelta, timezone

from job_agent.jobs import Job
from job_agent.tracking import diff_jobs, load_state, save_state

DAY0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _job(eid, title="Engineer", location="NYC"):
    return Job(external_id=eid, company="TestCo", ats="greenhouse", title=title, location=location, url=f"https://x/{eid}")


def _change(changes, eid):
    return next(c for c in changes if c.job.external_id == eid)


def test_first_run_marks_everything_new():
    _, changes = diff_jobs("TestCo", [_job("A"), _job("B")], {}, now=DAY0)
    assert {c.change for c in changes} == {"new"}
    assert _change(changes, "A").repost_count == 0
    assert _change(changes, "A").age_days == 0


def test_unchanged_job_stays_unchanged():
    state, _ = diff_jobs("TestCo", [_job("A")], {}, now=DAY0)
    _, changes = diff_jobs("TestCo", [_job("A")], state, now=DAY0 + timedelta(days=1))
    assert _change(changes, "A").change == "unchanged"
    assert _change(changes, "A").age_days == 1


def test_changed_field_is_reported_as_edited():
    state, _ = diff_jobs("TestCo", [_job("A", location="NYC")], {}, now=DAY0)
    _, changes = diff_jobs("TestCo", [_job("A", location="Remote")], state, now=DAY0 + timedelta(days=1))
    assert _change(changes, "A").change == "edited"


def test_missing_job_is_not_gone_after_only_one_miss():
    state, _ = diff_jobs("TestCo", [_job("A"), _job("C")], {}, now=DAY0)

    state, changes = diff_jobs("TestCo", [_job("A")], state, now=DAY0 + timedelta(days=1))

    assert all(c.job.external_id != "C" for c in changes)  # no change reported yet
    assert state["C"].status == "open"
    assert state["C"].misses == 1


def test_missing_job_is_gone_after_two_consecutive_misses():
    state, _ = diff_jobs("TestCo", [_job("A"), _job("C")], {}, now=DAY0)
    state, _ = diff_jobs("TestCo", [_job("A")], state, now=DAY0 + timedelta(days=1))

    state, changes = diff_jobs("TestCo", [_job("A")], state, now=DAY0 + timedelta(days=2))

    gone = _change(changes, "C")
    assert gone.change == "gone"
    assert state["C"].status == "closed"


def test_repost_under_same_external_id_increments_count_but_keeps_original_age():
    state, _ = diff_jobs("TestCo", [_job("A")], {}, now=DAY0)
    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=1))
    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=2))  # now closed
    assert state["A"].status == "closed"

    _, changes = diff_jobs("TestCo", [_job("A")], state, now=DAY0 + timedelta(days=10))

    reposted = _change(changes, "A")
    assert reposted.change == "repost"
    assert reposted.repost_count == 1
    assert reposted.age_days == 10  # counted from first_seen_at (day 0), not reset


def test_repost_under_a_new_external_id_with_same_title_and_location_is_detected():
    state, _ = diff_jobs("TestCo", [_job("C", "PM", "Remote")], {}, now=DAY0)
    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=1))
    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=2))  # C now closed

    _, changes = diff_jobs("TestCo", [_job("D", "PM", "Remote")], state, now=DAY0 + timedelta(days=5))

    reposted = _change(changes, "D")
    assert reposted.change == "repost"
    assert reposted.repost_count == 1
    assert reposted.age_days == 5  # inherited first_seen_at from the closed job it matched


def test_repost_count_keeps_incrementing_across_multiple_relistings():
    state, _ = diff_jobs("TestCo", [_job("A")], {}, now=DAY0)
    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=1))
    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=2))
    state, changes = diff_jobs("TestCo", [_job("A")], state, now=DAY0 + timedelta(days=5))
    assert _change(changes, "A").repost_count == 1

    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=9))
    state, _ = diff_jobs("TestCo", [], state, now=DAY0 + timedelta(days=10))
    _, changes = diff_jobs("TestCo", [_job("A")], state, now=DAY0 + timedelta(days=12))

    assert _change(changes, "A").repost_count == 2


def test_state_round_trips_through_disk(tmp_path):
    state, _ = diff_jobs("TestCo", [_job("A")], {}, now=DAY0)

    save_state("TestCo", state, jobs_dir=tmp_path)
    reloaded = load_state("TestCo", jobs_dir=tmp_path)

    assert reloaded == state
