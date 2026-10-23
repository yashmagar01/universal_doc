"""Ingestion job handler (FR-ING-03/21, architecture §6.3 + §12.3).

Runs the four stages on the job thread: probe (validate) -> sandboxed extract -> heuristic
build -> persist. Progress events use the §11 stage vocabulary; the handler returns silently
when `cancel` is set (the runner marks the job cancelled) and the template is only written to
the store once every stage has succeeded, so a cancelled/failed job leaves no half-template.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine

from ..api.jobs import Cancel, Emit, Handler
from ..store import BlobStore, put_template, transaction
from .errors import IngestError
from .pipeline import build_template
from .sandbox import run_worker

MANY_PAGES = 100000  # allowManyPages override: effectively "no limit" (FR-ING-01)


def make_ingest_handler(engine: Engine, blob: BlobStore) -> Handler:
    """Build the `ingest` job handler bound to a store engine and blob store."""

    def handler(payload: dict[str, Any], emit: Emit, cancel: Cancel) -> None:
        template_id = str(payload["templateId"])
        sha256 = str(payload["sha256"])
        file_name = str(payload["fileName"])
        name = str(payload.get("name") or Path(file_name).stem or "Untitled")
        max_pages = MANY_PAGES if payload.get("allowManyPages") else 0
        pdf_path = str(blob.path(sha256))

        with tempfile.TemporaryDirectory(prefix="templix-ingest-") as work:
            out_dir = Path(work)

            emit({"progress": 5, "stage": "validate", "message": "Reading document"})
            probe = run_worker("probe", pdf_path, max_pages=max_pages, cancel=cancel)
            if not probe.get("ok"):
                if probe.get("code") == "cancelled":
                    return
                raise IngestError(str(probe.get("code", "crash")))

            emit({"progress": 30, "stage": "extract", "message": "Extracting layers"})
            extract = run_worker(
                "extract", pdf_path, out_dir=str(out_dir), dpi=150,
                max_pages=max_pages, cancel=cancel,
            )
            if not extract.get("ok"):
                if extract.get("code") == "cancelled":
                    return
                raise IngestError(str(extract.get("code", "crash")))
            if int(extract.get("pageCount", 0)) != int(probe.get("pageCount", 0)):
                raise IngestError("corrupt")

            emit({"progress": 60, "stage": "build", "message": "Detecting layers"})
            template = build_template(
                extract,
                template_id=template_id,
                name=name,
                file_name=file_name,
                sha256=sha256,
                blob=blob,
                out_dir=out_dir,
            )
            if cancel.is_set():
                return

            emit({"progress": 95, "stage": "save", "message": "Saving template"})
            with transaction(engine) as conn:
                put_template(conn, template)

    return handler
