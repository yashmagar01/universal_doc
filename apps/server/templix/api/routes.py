"""REST endpoints: templates, documents, op-log patches, jobs (§11)."""

from __future__ import annotations

import asyncio
import json
import tempfile
from collections.abc import AsyncIterator, Iterator
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as dist_version
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from ..ingest.errors import MAX_PDF_BYTES, IngestError
from ..ingest.pipeline import confidence_of
from ..ingest.sandbox import run_worker
from ..ingest.validate import check_upload
from ..model import (
    SCHEMA_VERSION,
    Document,
    Node,
    NodeType,
    Patch,
    Run,
    Slot,
    Template,
    apply_patch,
    invert_patch,
    new_ulid,
)
from ..store import (
    BlobStore,
    append_op,
    get_document,
    get_template,
    list_documents,
    list_templates,
    next_seq,
    put_document,
    put_template,
    transaction,
)
from ..vault import SecretStore
from .jobs import JobRunner
from .security import COOKIE, HEADER, LAUNCH_HEADER

# §11: every system endpoint lives under the versioned base path.
router = APIRouter(prefix="/api/v1")


class DocumentCreate(BaseModel):
    templateId: str
    templateVersion: int | None = None


MAX_OPS = 1000
MAX_PATCH_BYTES = 128 * 1024


def _check_size(patch: Patch) -> None:
    """Reject oversized patches before touching the database (NFR payload limits)."""
    if len(patch.ops) > MAX_OPS:
        raise HTTPException(422, f"patch exceeds {MAX_OPS} ops")
    if len(patch.model_dump_json()) > MAX_PATCH_BYTES:
        raise HTTPException(413, f"patch exceeds {MAX_PATCH_BYTES} bytes")


def _walk(nodes: list[Node]) -> Iterator[Node]:
    for node in nodes:
        yield node
        if node.children:
            yield from _walk(node.children)


def _check_ownership(conn: Any, doc: Document, patch: Patch) -> None:
    """Every op must target a slot/node that belongs to the document's template.

    `apply()` is permissive (it would happily create a new slot key or override entry), so this
    is the guard that keeps ops scoped to entities the document actually owns.
    """
    tpl = get_template(conn, doc.templateId, doc.templateVersion)
    if tpl is None:
        raise HTTPException(422, "document template missing")
    slots = {s.id for s in tpl.slots}
    nodes = {n.id for page in tpl.pages for n in _walk(page.nodes)}
    for op in patch.ops:
        if op.kind in ("set_slot", "clear_slot") and op.slotId not in slots:
            raise HTTPException(422, f"slot {op.slotId} does not belong to this document")
        if op.kind in ("set_override", "remove_override") and op.nodeId not in nodes:
            raise HTTPException(422, f"node {op.nodeId} does not belong to this document")


def _engine(request: Request) -> Engine:
    # Starlette's `request.state` is request-scoped and NOT linked to `app.state`;
    # read the app's own state, which `create_app` populates before mounting the router.
    return request.app.state.engine


def _blob(request: Request) -> BlobStore:
    return request.app.state.blob


def _slot_runs(tpl: Template, slot: Slot) -> list[Run]:
    """Start a document from the template's own content (FR-TPL-18).

    Slots bind nodes; the first bound node carries the shared text for multi-page slots.
    Image slots have no runs and stay empty until image replacement exists.
    """
    nodes = {node.id: node for page in tpl.pages for node in _walk(page.nodes)}
    for node_id in slot.nodeIds:
        node = nodes.get(node_id)
        if node is not None and node.runs:
            return [run.model_copy(deep=True) for run in node.runs]
    return []


def _instantiate(tpl: Template) -> Document:
    doc = Document(id=new_ulid(), templateId=tpl.id, templateVersion=tpl.version)
    for slot in tpl.slots:
        doc.content.values[slot.id] = _slot_runs(tpl, slot)
    return doc


# --- system (§11) ---


def _package_version(dist: str, fallback: str) -> str:
    try:
        return dist_version(dist)
    except PackageNotFoundError:
        return fallback


@router.get("/status")
def status() -> dict[str, object]:
    """Live system facts for the footer (FR-SYS-02). RAM is null until a probe exists."""
    return {
        "schemaVersion": SCHEMA_VERSION,
        "state": "ok",
        "engine": "ready",
        "version": _package_version("templix-server", "0.1.0"),
        # Metadata-only lookup: the server must never import PyMuPDF (D-007 sandbox boundary).
        "parser": f"PDF Parser: PyMuPDF {_package_version('pymupdf', 'unknown')}",
        "ram": None,
        "privacyMode": "No telemetry",
    }


@router.post("/session")
def session(request: Request, response: Response) -> dict[str, str]:
    # Launch token == session token; this sets the SameSite=Strict cookie for browser flows.
    cfg = request.app.state.cfg
    if request.headers.get(LAUNCH_HEADER) != cfg.token and request.headers.get(HEADER) != cfg.token:
        raise HTTPException(401, "invalid launch token")
    response.set_cookie(COOKIE, cfg.token, samesite="strict", httponly=True, path="/")
    return {"token": cfg.token}


# --- templates ---


def _layer_count(nodes: list[Node]) -> int:
    """Count editable leaves; a nested group is a container, not one layer."""
    return sum(
        _layer_count(node.children or []) if node.type == NodeType.group else 1 for node in nodes
    )


@router.get("/templates")
def templates_list(request: Request) -> list[dict[str, Any]]:
    with transaction(_engine(request)) as conn:
        rows = list_templates(conn)
    out: list[dict[str, Any]] = []
    for row in rows:
        tpl = Template.model_validate_json(row["doc"])
        out.append(
            {
                "id": row["id"],
                "name": row["name"],
                "version": row["version"],
                "updatedAt": row["updated_at"],
                "pageCount": len(tpl.pages),
                "layerCount": sum(_layer_count(page.nodes) for page in tpl.pages),
                "status": "needs-review" if tpl.reviewItems else "ready",
            }
        )
    return out


@router.post("/templates/ingest", status_code=202)
async def templates_ingest(
    request: Request,
    file: UploadFile,
    allowManyPages: bool = Form(False),
    name: str | None = Form(None),
) -> dict[str, str]:
    """Accept a PDF upload and queue the ingestion job (FR-ING-01/03, §11)."""
    data = await file.read(MAX_PDF_BYTES + 1)
    try:
        check_upload(data)
    except IngestError as exc:
        status = 413 if exc.code == "file_too_large" else 400
        raise HTTPException(status, {"code": exc.code, "hint": exc.hint}) from exc
    blob = _blob(request)
    sha256 = blob.put(data)
    template_id = new_ulid()
    file_name = file.filename or "upload.pdf"
    job = _jobs(request).submit(
        "ingest",
        {
            "templateId": template_id,
            "sha256": sha256,
            "fileName": file_name,
            "name": name or file_name.rsplit(".", 1)[0],
            "allowManyPages": allowManyPages,
        },
    )
    return {"jobId": job.id, "templateId": template_id}


@router.post("/templates", status_code=201)
def templates_create(tpl: Template, request: Request) -> dict[str, Any]:
    with transaction(_engine(request)) as conn:
        try:
            put_template(conn, tpl)
        except IntegrityError as exc:
            raise HTTPException(409, "template id+version already exists") from exc
    return tpl.model_dump()


@router.get("/templates/{tpl_id}")
def templates_get(tpl_id: str, request: Request, version: int | None = None) -> dict[str, Any]:
    with transaction(_engine(request)) as conn:
        tpl = get_template(conn, tpl_id, version)
    if tpl is None:
        raise HTTPException(404, "template not found")
    return tpl.model_dump()


@router.get("/templates/{tpl_id}/analysis")
def templates_analysis(tpl_id: str, request: Request) -> dict[str, Any]:
    """Ingestion result for the analysis screen: template + overall confidence (§6.3 step 5)."""
    with transaction(_engine(request)) as conn:
        tpl = get_template(conn, tpl_id)
    if tpl is None:
        raise HTTPException(404, "template not found")
    return {"template": tpl.model_dump(), "confidence": confidence_of(tpl)}


@router.get("/templates/{tpl_id}/pages/{index}/reference.png")
def template_page_reference(tpl_id: str, index: int, request: Request) -> FileResponse:
    with transaction(_engine(request)) as conn:
        tpl = get_template(conn, tpl_id)
    if tpl is None or index < 0 or index >= len(tpl.pages):
        raise HTTPException(404, "page not found")
    sha = tpl.pages[index].referenceSha
    blob = _blob(request)
    if sha is None or not blob.exists(sha):
        raise HTTPException(404, "reference raster missing")
    return FileResponse(str(blob.path(sha)), media_type="image/png")


# --- documents ---


@router.get("/documents")
def documents_list(request: Request) -> list[dict[str, Any]]:
    with transaction(_engine(request)) as conn:
        return [
            {
                "id": r["id"],
                "templateId": r["template_id"],
                "templateVersion": r["template_version"],
                "status": r["status"],
                "updatedAt": r["updated_at"],
            }
            for r in list_documents(conn)
        ]


@router.post("/documents", status_code=201)
def documents_create(payload: DocumentCreate, request: Request) -> dict[str, Any]:
    with transaction(_engine(request)) as conn:
        tpl = get_template(conn, payload.templateId, payload.templateVersion)
        if tpl is None:
            raise HTTPException(404, "template not found")
        doc = _instantiate(tpl)
        put_document(conn, doc)
    return doc.model_dump()


@router.get("/documents/{doc_id}")
def documents_get(doc_id: str, request: Request) -> dict[str, Any]:
    with transaction(_engine(request)) as conn:
        doc = get_document(conn, doc_id)
    if doc is None:
        raise HTTPException(404, "document not found")
    return doc.model_dump()


@router.get("/documents/{doc_id}/export.pdf")
def documents_export(doc_id: str, request: Request) -> FileResponse:
    """Export the document by replacing only edited slot text on the source PDF.

    The PyMuPDF work runs in the ingest sandbox (D-007); this endpoint never imports it.
    """
    with transaction(_engine(request)) as conn:
        doc = get_document(conn, doc_id)
        tpl = get_template(conn, doc.templateId, doc.templateVersion) if doc else None
    if doc is None:
        raise HTTPException(404, "document not found")
    if tpl is None:
        raise HTTPException(409, "document template missing")
    source_sha = tpl.source.sha256
    blob = _blob(request)
    if source_sha is None or not blob.exists(source_sha):
        raise HTTPException(409, "source PDF unavailable for export")

    with tempfile.TemporaryDirectory(prefix="templix-export-") as work:
        out_path = Path(work) / "export.pdf"
        result = run_worker(
            "export",
            str(blob.path(source_sha)),
            out_dir=work,
            extra={
                "template": tpl.model_dump(mode="json"),
                "document": doc.model_dump(mode="json"),
                "outPdf": str(out_path),
            },
        )
        if not result.get("ok") or not out_path.is_file():
            raise HTTPException(
                500,
                {
                    "code": str(result.get("code", "export_failed")),
                    "hint": str(result.get("hint") or "PDF export failed"),
                },
            )
        warnings = [
            str(warning) for warning in cast(list[object], result.get("warnings") or [])
        ]
        if warnings:
            # Never hand back a PDF with edited text silently missing; ask for shorter text.
            raise HTTPException(
                422,
                {
                    "code": "text_overflow",
                    "hint": "; ".join(warnings),
                },
            )
        data = out_path.read_bytes()

    digest = blob.put(data)
    stem = "".join(c for c in (tpl.name or "document") if c.isalnum() or c in " -_").strip()
    return FileResponse(
        str(blob.path(digest)),
        media_type="application/pdf",
        filename=f"{stem or 'document'}.pdf",
    )


@router.post("/documents/{doc_id}/ops")
def documents_ops(doc_id: str, patch: Patch, request: Request) -> dict[str, Any]:
    """Apply a forward patch; persist it; return the new doc + the undo patch."""
    _check_size(patch)
    locked: frozenset[str] = frozenset()  # M1: no locked layers yet (preview locks arrive in M2)
    with transaction(_engine(request)) as conn:
        doc = get_document(conn, doc_id)
        if doc is None:
            raise HTTPException(404, "document not found")
        _check_ownership(conn, doc, patch)
        try:
            # invert_patch also applies each op while walking the pre-state, so both the
            # inversion and the forward pass can reject a bad patch (422, never 500).
            undo = invert_patch(doc, patch)
            forward = apply_patch(doc, patch, locked_nodes=locked)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        seq = next_seq(conn, doc_id)
        append_op(conn, doc_id, seq, patch.model_dump_json())
        forward.status = doc.status
        put_document(conn, forward)
    return {"document": forward.model_dump(), "undo": undo.model_dump(), "seq": seq}


# --- jobs (runner + SSE) ---


class JobCreate(BaseModel):
    kind: str
    payload: dict[str, Any] = {}


def _jobs(request: Request) -> JobRunner:
    return request.app.state.jobs


@router.post("/jobs", status_code=202)
def jobs_create(body: JobCreate, request: Request) -> dict[str, Any]:
    try:
        job = _jobs(request).submit(body.kind, body.payload)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"id": job.id, "kind": job.kind, "status": job.status}


@router.get("/jobs/{job_id}")
def jobs_get(job_id: str, request: Request) -> dict[str, Any]:
    job = _jobs(request).get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return {"id": job.id, "kind": job.kind, "status": job.status, "error": job.error}


@router.post("/jobs/{job_id}/cancel")
def jobs_cancel(job_id: str, request: Request) -> dict[str, Any]:
    """Signal a running job to stop (FR-ING-03); idempotent on an already-terminal job."""
    job = _jobs(request).cancel(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return {"id": job.id, "status": job.status, "cancelRequested": job.cancel.is_set()}


@router.get("/jobs/{job_id}/events")
async def jobs_events(job_id: str, request: Request) -> StreamingResponse:
    """Server-Sent Events for a job: each progress event, then close on the terminal one."""
    job = _jobs(request).get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")

    async def _gen() -> AsyncIterator[str]:
        sent = 0
        while True:
            while sent < len(job.events):
                yield f"data: {json.dumps(job.events[sent])}\n\n"
                sent += 1
            if job.terminal:
                break
            await asyncio.sleep(0.01)

    return StreamingResponse(_gen(), media_type="text/event-stream")


# --- provider config (write-only key) ---


class ProviderKeyIn(BaseModel):
    key: str


def _vault(request: Request) -> SecretStore:
    return request.app.state.vault


def _hint(key: str) -> str:
    """Write-only view: expose a masked tail, never the full key."""
    return f"...{key[-4:]}" if len(key) >= 4 else "..."


@router.put("/providers/{name}/key")
def provider_set_key(name: str, body: ProviderKeyIn, request: Request) -> dict[str, Any]:
    if not body.key:
        raise HTTPException(422, "empty api key")
    _vault(request).set(name, body.key)
    return {"provider": name, "configured": True}


@router.get("/providers/{name}")
def provider_get(name: str, request: Request) -> dict[str, Any]:
    key = _vault(request).get(name)
    if key is None:
        return {"provider": name, "configured": False, "hint": None}
    return {"provider": name, "configured": True, "hint": _hint(key)}


@router.delete("/providers/{name}/key")
def provider_delete_key(name: str, request: Request) -> dict[str, Any]:
    _vault(request).delete(name)
    return {"provider": name, "configured": False}
