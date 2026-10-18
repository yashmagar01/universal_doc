"""In-process job runner with SSE progress (§11; groundwork for the FR-ING-03 ingestion job).

A handler is ``handler(payload, emit)``; each ``emit(event)`` appends a progress event the SSE
stream delivers. The terminal event is ``{"status": "done"}`` (or ``{"status": "failed", ...}``).

ponytail: handlers run synchronously inside ``submit`` (M1 jobs are fast). Long M2 ingestion runs
move to a background thread/process without changing this surface — the endpoints already read
``job.events`` live, so streaming keeps working once execution is async.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

Emit = Callable[[dict[str, Any]], None]
Handler = Callable[[dict[str, Any], Emit], None]


class Job:
    def __init__(self, job_id: str, kind: str, payload: dict[str, Any]) -> None:
        self.id = job_id
        self.kind = kind
        self.payload = payload
        self.status = "queued"
        self.events: list[dict[str, Any]] = []
        self.error: str | None = None

    @property
    def terminal(self) -> bool:
        return self.status in ("done", "failed")


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
        job.status = "running"

        def emit(event: dict[str, Any]) -> None:
            job.events.append(event)

        try:
            handler(job.payload, emit)
        except Exception as exc:  # a failing job becomes a failed job, never a 500
            job.status = "failed"
            job.error = str(exc)
            job.events.append({"status": "failed", "error": str(exc)})
            return job
        job.status = "done"
        job.events.append({"status": "done"})
        return job


def _demo_handler(payload: dict[str, Any], emit: Emit) -> None:
    """Built-in ``echo`` job: emits deterministically so SSE can be exercised end-to-end."""
    steps = int(payload.get("steps", 3))
    for i in range(1, steps + 1):
        emit({"progress": int(i * 100 / steps), "step": i})
    if payload.get("fail"):
        raise RuntimeError("demo failure")


def default_runner() -> JobRunner:
    runner = JobRunner()
    runner.register("echo", _demo_handler)
    return runner
