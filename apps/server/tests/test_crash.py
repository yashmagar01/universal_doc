"""Crash-durability tests (NFR-REL-01): a force-killed writer never corrupts the DB.

Simulates `kill -9` by force-terminating a child process (Windows: `TerminateProcess`) while it
holds an open write transaction. After the kill, the committed rows must survive WAL recovery,
the uncommitted row must be gone, and `PRAGMA integrity_check` must report `ok`.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from sqlalchemy import select, text

from templix.store import get_engine, init_db
from templix.store.db import documents

# Child: commit one row, start a second (uncommitted) tx, signal readiness, then hang.
_CHILD = """
import sqlite3, sys, time
from pathlib import Path
db, sentinel = sys.argv[1], sys.argv[2]
c = sqlite3.connect(db, isolation_level=None)
c.execute("PRAGMA journal_mode=WAL")
c.execute("BEGIN")
c.execute("INSERT INTO documents VALUES ('committed-doc','t',1,'draft',1,'{}','now')")
c.execute("COMMIT")
c.execute("BEGIN")
c.execute("INSERT INTO documents VALUES ('uncommitted-doc','t',1,'draft',1,'{}','now')")
Path(sentinel).write_text("ready")
time.sleep(1000)
"""


def _make_db(db: Path) -> None:
    engine = get_engine(f"sqlite:///{db.as_posix()}")
    init_db(engine)
    engine.dispose()


def _inspect(db: Path) -> tuple[set[str], object]:
    engine = get_engine(f"sqlite:///{db.as_posix()}")
    with engine.connect() as conn:
        ids = {str(r[0]) for r in conn.execute(select(documents.c.id))}
        check = conn.execute(text("PRAGMA integrity_check")).scalar()
    engine.dispose()
    return ids, check


def test_kill9_recovers_wal(tmp_path: Path) -> None:
    db = tmp_path / "crash.db"
    sentinel = tmp_path / "ready"
    _make_db(db)

    proc = subprocess.Popen(
        [sys.executable, "-c", _CHILD, str(db), str(sentinel)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.time() + 15
        while time.time() < deadline and not sentinel.exists():
            time.sleep(0.05)
        assert sentinel.exists(), "child writer never reached its committed state"
    finally:
        proc.kill()  # the crash: no clean close, no checkpoint
        proc.wait(timeout=10)

    ids, check = _inspect(db)
    assert "committed-doc" in ids, "committed write must survive a kill -9 (WAL recovery)"
    assert "uncommitted-doc" not in ids, "open transaction must be rolled back"
    assert check == "ok", f"integrity_check failed: {check}"
