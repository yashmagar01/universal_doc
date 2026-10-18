"""Forward-only migrations with automatic pre-migrate backup (NFR-REL-03).

`upgrade_head` copies the SQLite file aside (WAL-safe: the `.db`, plus `-wal`/`-shm` if present)
and then runs `alembic upgrade head` in a child process, so a failed migration never destroys data
and alembic's logging config stays out of the host process.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# apps/server (this file lives at apps/server/templix/store/migrate.py)
_SERVER_ROOT = Path(__file__).resolve().parents[2]


def backup_db(db_path: Path) -> Path | None:
    """Snapshot `db_path` (+ WAL sidecars) to a timestamped sibling. None if no DB yet."""
    if not db_path.exists():
        return None
    stamp = int(time.time())
    backup: Path | None = None
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(db_path) + suffix)
        if src.exists():
            dest = src.with_name(src.name + f".bak-{stamp}")
            shutil.copy2(src, dest)
            if not suffix:
                backup = dest
    return backup


def upgrade_head(db_path: Path) -> Path | None:
    """Back up the DB, then bring it to the current schema. Returns the backup path (or None)."""
    backup = backup_db(db_path)
    url = f"sqlite:///{db_path.resolve().as_posix()}"
    env = {**os.environ, "TEMPLIX_DB_URL": url}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_SERVER_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return backup
