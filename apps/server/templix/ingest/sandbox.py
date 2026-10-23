"""Resource-limited sandbox for PDF parsing (FR-ING-01/02, NFR-SEC-04, architecture §6.2).

The native worker (`python -m templix.ingest.native`) is treated as hostile territory:

- **wall clock** — `Popen.wait(timeout)`; on expiry the child is killed -> `timeout` (and POSIX
  additionally gets `RLIMIT_CPU` as a backstop — Windows has no per-process CPU rlimit; the
  worker never opens a network socket either).
- **memory** — Windows: a Job Object with `JOB_OBJECT_LIMIT_PROCESS_MEMORY` (+ kill-on-close so
  orphans die with us). POSIX: `RLIMIT_AS` applied via `preexec_fn` between fork and exec.
- **output** — result JSON + raster/image dir are size-capped so a hostile PDF cannot fill disk.
- **isolation** — the parent never imports `fitz` and never parses PDFs itself (D-007).

`ponytail:` Windows assigns the job right after `Popen`, so a child that allocates gigabytes in
its first few milliseconds could slip past the cap. PyMuPDF is not imported until after the
payload is read, and extraction — the expensive part — always runs under the job. Early-kill
only if this ever becomes a real problem.
"""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .errors import HINTS

# Windows NTSTATUS as seen unsigned (GetExitCodeProcess) or signed (Python), plus POSIX:
# 3 = worker MemoryError, -9 = SIGKILL from RLIMIT_CPU.
_LIMIT_EXIT_CODES = {3, 0xC0000017, 0xC00000A3, -1073741819, -1073741541, -9}

_K32: Any = cast(Any, ctypes).windll.kernel32 if os.name == "nt" else None


@dataclass(frozen=True)
class Limits:
    wall_clock_s: float = 60.0
    memory_mb: int = 2048  # parse headroom for 50 pages; generous so normal docs never trip it
    max_output_bytes: int = 64 * 1024 * 1024

    @property
    def memory_bytes(self) -> int:
        return self.memory_mb * 1024 * 1024


def run_worker(
    mode: str,
    pdf: str,
    *,
    out_dir: str | None = None,
    dpi: int = 150,
    max_pages: int = 0,
    limits: Limits | None = None,
    cancel: threading.Event | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Spawn the worker under `limits` and return its result dict.

    Always returns `{"ok": False, "code": <ingest code>, "hint": ...}` on failure — never raises
    a bare exception — so job records and API responses share one vocabulary (`errors.py`).
    `cancel` is polled every 100 ms; a set event kills the worker -> `cancelled`.
    """
    limits = limits or Limits()
    with tempfile.TemporaryDirectory(prefix="templix-sbx-") as tmp:
        in_path = Path(tmp) / "in.json"
        out_path = Path(tmp) / "out.json"
        err_path = Path(tmp) / "err.txt"
        payload: dict[str, Any] = {"mode": mode, "pdf": pdf, "maxPages": max_pages}
        if out_dir is not None:
            payload["outDir"] = out_dir
            payload["dpi"] = dpi
        if extra:
            payload.update(extra)
        in_path.write_text(json.dumps(payload), encoding="utf-8")

        cmd = [sys.executable, "-m", "templix.ingest.native", str(in_path), str(out_path)]
        started = time.monotonic()
        with err_path.open("wb") as err_file:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=err_file,
                env=_child_env(),
                **_spawn_kwargs(limits),
            )
        job_handle = _windows_job(proc, limits) if os.name == "nt" else None
        try:
            outcome = _wait_for_exit(proc, limits.wall_clock_s, cancel)
            rc = proc.returncode if proc.returncode is not None else 0
        finally:
            if job_handle is not None:
                _K32.CloseHandle(job_handle)  # KILL_ON_JOB_CLOSE reaps orphans

        if outcome == "cancelled":
            return {"ok": False, "code": "cancelled", "hint": "cancelled"}

        killed = outcome == "timeout"
        if not killed and rc == 0 and out_path.is_file():
            raw = out_path.read_text(encoding="utf-8", errors="replace")
            if len(raw) > limits.max_output_bytes:
                return _fail("limit")
            try:
                loaded: Any = json.loads(raw)
            except json.JSONDecodeError:
                return _fail("crash")
            if not isinstance(loaded, dict):
                return _fail("crash")
            result = cast(dict[str, Any], loaded)
            result.setdefault("hint", HINTS.get(str(result.get("code", "")), ""))
            result["elapsedS"] = round(time.monotonic() - started, 3)
            if (
                result.get("ok")
                and out_dir is not None
                and _dir_bytes(Path(out_dir)) > limits.max_output_bytes
            ):
                return _fail("limit")
            return result

        code = "timeout" if killed else ("limit" if rc in _LIMIT_EXIT_CODES else "crash")
        if code == "crash":
            _log_crash(err_path, rc)
        return _fail(code)


def _wait_for_exit(
    proc: subprocess.Popen[Any], timeout_s: float, cancel: threading.Event | None
) -> str:
    """Wait in 100 ms slices: "done" | "timeout" | "cancelled" (child killed on the last two)."""
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            proc.wait(timeout=0.1)
            return "done"
        except subprocess.TimeoutExpired:
            if cancel is not None and cancel.is_set():
                proc.kill()
                proc.wait(timeout=10)
                return "cancelled"
            if time.monotonic() >= deadline:
                proc.kill()
                proc.wait(timeout=10)
                return "timeout"


def _fail(code: str) -> dict[str, Any]:
    return {"ok": False, "code": code, "hint": HINTS[code]}


def _child_env() -> dict[str, str]:
    # Guarantee `import templix` regardless of how the parent was launched (D-007 stays local).
    server_root = str(Path(__file__).resolve().parents[2])
    env = dict(os.environ)
    env["PYTHONPATH"] = server_root + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _spawn_kwargs(limits: Limits) -> dict[str, Any]:
    """POSIX: rlimits must be set between fork and exec — so they ride on `Popen` itself."""
    if os.name != "posix":
        return {}

    def apply() -> None:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
        cpu_limit = max(int(limits.wall_clock_s), 1) + 1
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    return {"preexec_fn": apply}


def _windows_job(proc: subprocess.Popen[Any], limits: Limits) -> int | None:
    """Assign `proc` to a Job Object capped at `limits.memory_bytes`. Returns the job handle."""

    class IoCounters(ctypes.Structure):
        _fields_ = [
            (n, ctypes.c_uint64)
            for n in (
                "ReadOperationCount",
                "WriteOperationCount",
                "OtherOperationCount",
                "ReadTransferCount",
                "WriteTransferCount",
                "OtherTransferCount",
            )
        ]

    class BasicLimitInfo(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class ExtendedLimitInfo(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInfo),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JobObjectExtendedLimitInformation = 9

    job = _K32.CreateJobObjectW(None, None)
    if not job:
        return None
    info = ExtendedLimitInfo()
    info.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )
    info.ProcessMemoryLimit = limits.memory_bytes
    ok = bool(
        _K32.SetInformationJobObject(
            job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)
        )
    )
    # Child may already have exited (fast probes) — a failed assignment is harmless.
    # `._handle` exists only on Windows; cast(Any, ...) keeps pyright strict out of ctypes land.
    ok = ok and bool(_K32.AssignProcessToJobObject(job, int(cast(Any, proc)._handle)))
    if not ok:
        _K32.CloseHandle(job)
        return None
    return int(job)


def _dir_bytes(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _log_crash(err_path: Path, rc: int) -> None:
    try:
        tail = err_path.read_text(encoding="utf-8", errors="replace")[-2000:]
    except OSError:
        return
    print(f"[templix:ingest] worker exited rc={rc}:\n{tail}", file=sys.stderr)


__all__ = ["Limits", "run_worker"]
