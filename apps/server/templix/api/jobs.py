"""In-process job runner with SSE progress and cooperative cancel (§11, FR-ING-03).

A handler is ``handler(payload, emit, cancel)``; each ``emit(event)`` appends a progress event the
SSE stream delivers. Terminal states are ``done``, ``failed`` and ``cancelled``.

Handlers run on a daemon thread, so a long ingestion job never blocks the request that submitted
it (D-032). ``cancel`` is a :class:`threading.Event` the handler polls — the runner marks the job
cancelled once the handler returns.

ponytail: plain dict/list mutation under the GIL, no locks; job state is a handful of atomic
attribute writes read by a polling SSE loop. Replace with a queue+lock only if events ever race.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

Emit = Callable[[dict[str, Any]], None]
Cancel = threading.Event
Handler = Callable[[dict[str, Any], Emit, Cancel], None]

TERMINAL = ("done", "failed", "cancelled")
MAX_TERMINAL_JOBS = 100  # keep recent history bounded; running jobs are never pruned


class Job:
    def __init__(self, job_id: str, kind: str, payload: dict[str, Any]) -> None:
        self.id = job_id
        self.kind = kind
        self.payload = payload
        self.status = "queued"
        self.events: list[dict[str, Any]] = []
        self.error: str | None = None
        self.cancel = threading.Event()

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL


class JobRunner:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._handlers: dict[str, Handler] = {}

    def register(self, kind: str, handler: Handler) -> None:
        self._handlers[kind] = handler

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def submit(self, kind: str, payload: dict[str, Any] | None = None) -> Job:
        handler = self._handlers.get(kind)
        if handler is None:
            raise KeyError(f"unknown job kind {kind!r}")
        job = Job(job_id=uuid.uuid4().hex, kind=kind, payload=payload or {})
        self._jobs[job.id] = job
        self._prune()
        threading.Thread(
            target=self._run, args=(job, handler), name=f"job-{job.id[:8]}", daemon=True
        ).start()
        return job

    def _prune(self) -> None:
        """Drop the oldest terminal jobs so a long session cannot grow without bound."""
        terminal = [job_id for job_id, job in self._jobs.items() if job.terminal]
        for job_id in terminal[: max(0, len(terminal) - MAX_TERMINAL_JOBS)]:
            del self._jobs[job_id]

    def cancel(self, job_id: str) -> Job | None:
        """Ask a running job to stop; returns the job, or ``None`` when unknown."""
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if not job.terminal:
            job.cancel.set()
        return job

    def _run(self, job: Job, handler: Handler) -> None:
        job.status = "running"

        def emit(event: dict[str, Any]) -> None:
            job.events.append(event)

        try:
            handler(job.payload, emit, job.cancel)
        except Exception as exc:  # a failing job becomes a failed job, never a 500
            job.error = str(exc)
            if job.cancel.is_set():  # interrupted teardown (killed worker) is a cancel, not a failure
                self._finish(job, "cancelled", {"status": "cancelled", "reason": str(exc)})
            else:
                self._finish(job, "failed", {"status": "failed", "error": str(exc)})
            return
        if job.cancel.is_set():
            self._finish(job, "cancelled", {"status": "cancelled"})
        else:
            self._finish(job, "done", {"status": "done"})

    def _finish(self, job: Job, status: str, event: dict[str, Any]) -> None:
        job.status = status
        job.events.append(event)
        self._prune()


def _demo_handler(payload: dict[str, Any], emit: Emit, cancel: Cancel) -> None:
    """Built-in ``echo`` job: emits deterministically so SSE can be exercised end-to-end."""
    steps = int(payload.get("steps", 3))
    delay = float(payload.get("delay", 0))
    for i in range(1, steps + 1):
        if cancel.is_set():
            return
        emit({"progress": int(i * 100 / steps), "step": i})
        if delay:
            time.sleep(delay)
    if payload.get("fail"):
        raise RuntimeError("demo failure")


def default_runner() -> JobRunner:
    runner = JobRunner()
    runner.register("echo", _demo_handler)
    return runner
