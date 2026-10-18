"""Migration tests (NFR-REL-03): forward-only upgrades from scratch, with pre-migrate backup."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, inspect

from templix.store.migrate import upgrade_head

EXPECTED_TABLES = {"templates", "documents", "op_log", "jobs", "blobs", "alembic_version"}


def _tables(db: Path) -> set[str]:
    eng = create_engine(f"sqlite:///{db.as_posix()}")
    with eng.connect() as conn:
        return set(inspect(conn).get_table_names())


def test_upgrade_head_from_scratch(tmp_path: Path) -> None:
    db = tmp_path / "fresh.db"
    assert upgrade_head(db) is None  # no prior DB -> nothing to back up
    assert _tables(db) >= EXPECTED_TABLES

    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
    assert row is not None and str(row[0])  # stamped at head


def test_backup_created_before_upgrade(tmp_path: Path) -> None:
    db = tmp_path / "existing.db"
    upgrade_head(db)  # materialise the file
    backup = upgrade_head(db)  # now a pre-migrate snapshot must be taken
    assert backup is not None and backup.exists()
    assert _tables(Path(backup)) >= EXPECTED_TABLES  # the backup is itself a usable DB


def test_migration_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "idem.db"
    upgrade_head(db)
    first = _tables(db)
    upgrade_head(db)
    assert _tables(db) == first
