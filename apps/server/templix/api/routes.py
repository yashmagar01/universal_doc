"""REST endpoints: templates, documents, op-log patches, jobs (§11)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from ..model import Document, Patch, Template, apply_patch, invert_patch, new_ulid
from ..store import (
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

router = APIRouter()


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


def _check_ownership(conn: Any, doc: Document, patch: Patch) -> None:
    """Every op must target a slot/node that belongs to the document's template.

    `apply()` is permissive (it would happily create a new slot key or override entry), so this
    is the guard that keeps ops scoped to entities the document actually owns.
    """
    tpl = get_template(conn, doc.templateId, doc.templateVersion)
    if tpl is None:
        raise HTTPException(422, "document template missing")
    slots = {s.id for s in tpl.slots}
    nodes = {n.id for page in tpl.pages for n in page.nodes}
    for op in patch.ops:
        if op.kind in ("set_slot", "clear_slot") and op.slotId not in slots:
            raise HTTPException(422, f"slot {op.slotId} does not belong to this document")
        if op.kind in ("set_override", "remove_override") and op.nodeId not in nodes:
            raise HTTPException(422, f"node {op.nodeId} does not belong to this document")


def _engine(request: Request) -> Engine:
    # Starlette's `request.state` is request-scoped and NOT linked to `app.state`;
    # read the app's own state, which `create_app` populates before mounting the router.
    return request.app.state.engine


def _instantiate(tpl: Template) -> Document:
    doc = Document(id=new_ulid(), templateId=tpl.id, templateVersion=tpl.version)
    for slot in tpl.slots:
        doc.content.values[slot.id] = []
    return doc


# --- templates ---


@router.get("/templates")
def templates_list(request: Request) -> list[dict[str, Any]]:
    with transaction(_engine(request)) as conn:
        return [
            {"id": r["id"], "name": r["name"], "version": r["version"], "updatedAt": r["updated_at"]}
            for r in list_templates(conn)
        ]


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
        undo = invert_patch(doc, patch)
        try:
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
