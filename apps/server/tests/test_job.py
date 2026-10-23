"""The ingest job handler end-to-end against the store (FR-ING-03/21)."""

from __future__ import annotations

import time
from pathlib import Path

from sqlalchemy.engine import Engine

from templix.api.jobs import MAX_TERMINAL_JOBS, Job, JobRunner
from templix.ingest.job import make_ingest_handler
from templix.store import BlobStore, get_engine, get_template, init_db, list_templates, transaction

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "generated"


def _run(tmp_path: Path, fixture: str) -> tuple[Job, BlobStore, Engine]:
    engine = get_engine(f"sqlite:///{(tmp_path / 'templix.db').as_posix()}")
    init_db(engine)
    blob = BlobStore(tmp_path / "blobs")
    runner = JobRunner()
    runner.register("ingest", make_ingest_handler(engine, blob))
    data = (FIXTURES / fixture).read_bytes()
    sha = blob.put(data)
    job = runner.submit(
        "ingest",
        {
            "templateId": "01HZZZZZZZZZZZZZZZZZZZZZZA",
            "sha256": sha,
            "fileName": fixture,
            "name": "Newsletter",
        },
    )
    deadline = time.monotonic() + 60
    while not job.terminal and time.monotonic() < deadline:
        time.sleep(0.05)
    return job, blob, engine


def test_runner_bounds_terminal_job_history() -> None:
    runner = JobRunner()
    runner.register("noop", lambda _payload, _emit, _cancel: None)

    jobs: list[Job] = []
    for _ in range(MAX_TERMINAL_JOBS + 1):
        job = runner.submit("noop")
        jobs.append(job)
        deadline = time.monotonic() + 5
        while not job.terminal and time.monotonic() < deadline:
            time.sleep(0.001)
        assert job.terminal

    assert runner.get(jobs[0].id) is None  # oldest terminal job was pruned
    assert runner.get(jobs[-1].id) is jobs[-1]


def test_ingest_job_persists_template(tmp_path: Path) -> None:
    job, _blob, engine = _run(tmp_path, "newsletter_2col.pdf")
    assert job.status == "done", job.error
    assert [event["progress"] for event in job.events if "progress" in event] == [5, 30, 60, 95]
    assert job.events[-1]["status"] == "done"
    with transaction(engine) as conn:
        stored = get_template(conn, "01HZZZZZZZZZZZZZZZZZZZZZZA")
        rows = list_templates(conn)
    assert stored is not None
    assert stored.name == "Newsletter"
    assert len(stored.pages) == 2
    assert stored.slots
    assert stored.source.sha256
    assert len(rows) == 1


def test_ingest_job_fails_cleanly_on_malformed(tmp_path: Path) -> None:
    job, _blob, engine = _run(tmp_path, "malformed.pdf")
    assert job.status == "failed"
    assert job.error is not None and job.error.startswith("corrupt")
    with transaction(engine) as conn:
        assert get_template(conn, "01HZZZZZZZZZZZZZZZZZZZZZZA") is None


def test_ingest_job_fails_cleanly_on_encrypted(tmp_path: Path) -> None:
    job, _blob, _engine = _run(tmp_path, "encrypted.pdf")
    assert job.status == "failed"
    assert job.error is not None and job.error.startswith("encrypted")
