"""SQLite persistence via SQLAlchemy Core (architecture §4 "Store", §5.7).

Rows are JSON-backed documents plus a few scalar columns — Core avoids ORM descriptor typing
while keeping schema/migrations explicit. Every table carries `schema_version` (§5.7).
Atomicity: SQLite in WAL mode; single-statement transactions per request (NFR-REL-01/02).
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, create_engine, select
from sqlalchemy.engine import Engine

from ..model import SCHEMA_VERSION, Document, Template

metadata = MetaData()

# monotonic rowid-free ULID ids; `updated_at` set by _now()
templates = Table(
    "templates",
    metadata,
    Column("id", String, primary_key=True),
    Column("version", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("schema_version", Integer, nullable=False),
    Column("doc", Text, nullable=False),
    Column("updated_at", String, nullable=False),
)

documents = Table(
    "documents",
    metadata,
    Column("id", String, primary_key=True),
    Column("template_id", String, nullable=False),
    Column("template_version", Integer, nullable=False),
    Column("status", String, nullable=False),
    Column("schema_version", Integer, nullable=False),
    Column("doc", Text, nullable=False),
    Column("updated_at", String, nullable=False),
)

op_log = Table(
    "op_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", String, nullable=False, index=True),
    Column("seq", Integer, nullable=False),
    Column("patch", Text, nullable=False),
    Column("created_at", String, nullable=False),
)

jobs = Table(
    "jobs",
    metadata,
    Column("id", String, primary_key=True),
    Column("kind", String, nullable=False),
    Column("status", String, nullable=False),
    Column("payload", Text, nullable=False),
    Column("result", Text),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
)

blobs = Table(
    "blobs",
    metadata,
    Column("sha256", String, primary_key=True),
    Column("path", String, nullable=False),
    Column("size", Integer, nullable=False),
    Column("created_at", String, nullable=False),
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def get_engine(url: str = "sqlite:///templix.db") -> Engine:
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )
    if url.startswith("sqlite"):
        # WAL + busy_timeout: concurrent readers don't block the writer (NFR-REL-01/02)
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def _set_pragma(dbapi_conn: Any, _rec: Any) -> None:
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


def init_db(engine: Engine) -> None:
    metadata.create_all(engine)


@contextmanager
def transaction(engine: Engine) -> Generator[Any, None, None]:
    with engine.begin() as conn:
        yield conn


# --- templates (versioned) ---


def put_template(conn: Any, tpl: Template) -> None:
    conn.execute(
        templates.insert().values(
            id=tpl.id,
            version=tpl.version,
            name=tpl.name,
            schema_version=SCHEMA_VERSION,
            doc=tpl.model_dump_json(),
            updated_at=_now(),
        )
    )


def list_templates(conn: Any) -> list[dict[str, Any]]:
    rows = conn.execute(select(templates).order_by(templates.c.updated_at.desc())).mappings().all()
    return [dict(r) for r in rows]


def get_template(conn: Any, tpl_id: str, version: int | None = None) -> Template | None:
    stmt = select(templates).where(templates.c.id == tpl_id)
    if version is not None:
        stmt = stmt.where(templates.c.version == version)
    row = conn.execute(stmt.order_by(templates.c.version.desc()).limit(1)).mappings().first()
    if row is None:
        return None
    return Template.model_validate_json(row["doc"])


# --- documents ---


def put_document(conn: Any, doc: Document) -> None:
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    stmt = sqlite_insert(documents).values(
        id=doc.id,
        template_id=doc.templateId,
        template_version=doc.templateVersion,
        status=doc.status.value,
        schema_version=SCHEMA_VERSION,
        doc=doc.model_dump_json(),
        updated_at=_now(),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[documents.c.id],
        set_={
            "doc": stmt.excluded.doc,
            "status": stmt.excluded.status,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    conn.execute(stmt)


def get_document(conn: Any, doc_id: str) -> Document | None:
    row = conn.execute(select(documents).where(documents.c.id == doc_id)).mappings().first()
    return Document.model_validate_json(row["doc"]) if row else None


def list_documents(conn: Any) -> list[dict[str, Any]]:
    rows = conn.execute(select(documents).order_by(documents.c.updated_at.desc())).mappings().all()
    return [dict(r) for r in rows]


def append_op(conn: Any, doc_id: str, seq: int, patch_json: str) -> None:
    conn.execute(
        op_log.insert().values(document_id=doc_id, seq=seq, patch=patch_json, created_at=_now())
    )


def ops_for(conn: Any, doc_id: str) -> list[dict[str, Any]]:
    rows = (
        conn.execute(select(op_log).where(op_log.c.document_id == doc_id).order_by(op_log.c.seq))
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def next_seq(conn: Any, doc_id: str) -> int:
    from sqlalchemy import func

    max_seq = func.max(op_log.c.seq)
    cur = conn.execute(select(func.coalesce(max_seq, 0)).where(op_log.c.document_id == doc_id)).scalar()
    return int(cur or 0) + 1
