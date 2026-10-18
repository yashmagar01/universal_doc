"""Endpoint-level API tests: status, session, templates, documents, ops (§11)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from fastapi.testclient import TestClient

from templix.api.routes import MAX_OPS, MAX_PATCH_BYTES
from templix.model import BBox, Node, NodeType, Page, Size, Slot, SlotKind, Template, new_ulid
from tests.conftest import TOKEN


def make_template(name: str = "Invoice") -> tuple[Template, str]:
    slot = Slot(id=new_ulid(), nodeIds=[new_ulid()], label="Title", kind=SlotKind.text)
    tpl = Template(id=new_ulid(), name=name, slots=[slot])
    return tpl, slot.id


def make_template_with_node() -> tuple[Template, str, str]:
    node_id = new_ulid()
    node = Node(id=node_id, type=NodeType.text, role="title", bbox=BBox(x=0, y=0, w=10, h=10))
    page = Page(id=new_ulid(), size=Size(w=100, h=100), nodes=[node])
    slot = Slot(id=new_ulid(), nodeIds=[node_id], label="Title", kind=SlotKind.text)
    return Template(id=new_ulid(), name="Doc", slots=[slot], pages=[page]), slot.id, node_id


def _seed(client: TestClient, tpl: Template) -> str:
    client.post("/templates", json=tpl.model_dump(mode="json"))
    doc = client.post("/documents", json={"templateId": tpl.id}).json()
    return str(doc["id"])


def test_status_requires_token(client: TestClient) -> None:
    r = client.get("/status", headers={"X-Templix-Token": ""})
    assert r.status_code == 401


def test_status_ok(client: TestClient) -> None:
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json()["schemaVersion"] == 1


def test_security_headers_present(client: TestClient) -> None:
    h = client.get("/status").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["content-security-policy"] == "default-src 'self'"


def test_session_sets_strict_cookie(client: TestClient) -> None:
    r = client.post("/session", headers={"X-Templix-Launch-Token": TOKEN})
    assert r.status_code == 200
    assert "templix_session" in r.cookies


def test_template_crud(client: TestClient) -> None:
    tpl, _ = make_template()
    r = client.post("/templates", json=tpl.model_dump(mode="json"))
    assert r.status_code == 201

    listed = client.get("/templates").json()
    assert any(t["id"] == tpl.id for t in listed)

    got = client.get(f"/templates/{tpl.id}")
    assert got.status_code == 200
    assert got.json()["name"] == "Invoice"

    dup = client.post("/templates", json=tpl.model_dump(mode="json"))
    assert dup.status_code == 409


def test_document_create_and_ops_roundtrip(client: TestClient) -> None:
    tpl, slot_id = make_template()
    client.post("/templates", json=tpl.model_dump(mode="json"))

    doc = client.post("/documents", json={"templateId": tpl.id}).json()
    assert doc["content"]["values"][slot_id] == []

    patch: dict[str, Any] = {
        "ops": [{"kind": "set_slot", "slotId": slot_id, "value": [{"text": "Hello"}]}]
    }
    applied = client.post(f"/documents/{doc['id']}/ops", json=patch)
    assert applied.status_code == 200
    body: Mapping[str, Any] = applied.json()
    assert body["document"]["content"]["values"][slot_id] == [{"text": "Hello", "marks": []}]
    assert body["seq"] == 1

    undo = client.post(f"/documents/{doc['id']}/ops", json=body["undo"])
    assert undo.status_code == 200
    assert undo.json()["document"]["content"]["values"][slot_id] == []


def test_document_not_found(client: TestClient) -> None:
    assert client.get("/documents/NOPE").status_code == 404
    assert client.post("/documents", json={"templateId": "NOPE"}).status_code == 404


def test_ops_rejects_slot_not_owned_by_document(client: TestClient) -> None:
    tpl, _ = make_template()
    doc_id = _seed(client, tpl)
    patch: dict[str, Any] = {"ops": [{"kind": "set_slot", "slotId": "nope", "value": []}]}
    r = client.post(f"/documents/{doc_id}/ops", json=patch)
    assert r.status_code == 422
    assert "does not belong" in str(r.json()["detail"])


def test_ops_rejects_node_not_owned_by_document(client: TestClient) -> None:
    tpl, _, _ = make_template_with_node()
    doc_id = _seed(client, tpl)
    op = {"kind": "set_override", "nodeId": "nope", "prop": "fill", "value": "#ff0000"}
    r = client.post(f"/documents/{doc_id}/ops", json={"ops": [op]})
    assert r.status_code == 422
    assert "does not belong" in str(r.json()["detail"])


def test_ops_override_on_owned_node(client: TestClient) -> None:
    tpl, _, node_id = make_template_with_node()
    doc_id = _seed(client, tpl)
    op = {"kind": "set_override", "nodeId": node_id, "prop": "fill", "value": "#ff0000"}
    r = client.post(f"/documents/{doc_id}/ops", json={"ops": [op]})
    assert r.status_code == 200
    assert r.json()["document"]["overrides"][node_id]["fill"] == "#ff0000"


def test_ops_rejects_too_many_ops(client: TestClient) -> None:
    tpl, slot_id = make_template()
    doc_id = _seed(client, tpl)
    ops: list[dict[str, Any]] = [
        {"kind": "set_slot", "slotId": slot_id, "value": []} for _ in range(MAX_OPS + 1)
    ]
    r = client.post(f"/documents/{doc_id}/ops", json={"ops": ops})
    assert r.status_code == 422
    assert f"{MAX_OPS} ops" in str(r.json()["detail"])


def test_ops_rejects_oversized_patch(client: TestClient) -> None:
    tpl, slot_id = make_template()
    doc_id = _seed(client, tpl)
    big = [{"kind": "set_slot", "slotId": slot_id, "value": [{"text": "x" * 200_000}]}]
    r = client.post(f"/documents/{doc_id}/ops", json={"ops": big})
    assert r.status_code == 413
    assert f"{MAX_PATCH_BYTES} bytes" in str(r.json()["detail"])


# --- jobs ---


def test_job_unknown_kind_404(client: TestClient) -> None:
    assert client.post("/jobs", json={"kind": "nope"}).status_code == 404


def test_job_not_found(client: TestClient) -> None:
    assert client.get("/jobs/NOPE").status_code == 404
    assert client.get("/jobs/NOPE/events").status_code == 404


def test_job_submit_and_status(client: TestClient) -> None:
    r = client.post("/jobs", json={"kind": "echo", "payload": {"steps": 3}})
    assert r.status_code == 202
    job_id = r.json()["id"]
    status = client.get(f"/jobs/{job_id}").json()
    assert status["status"] == "done"
    assert status["error"] is None


def test_job_failure_is_reported_not_raised(client: TestClient) -> None:
    r = client.post("/jobs", json={"kind": "echo", "payload": {"steps": 1, "fail": True}})
    assert r.status_code == 202
    status = client.get(f"/jobs/{r.json()['id']}").json()
    assert status["status"] == "failed"
    assert "demo failure" in status["error"]


def test_job_sse_streams_progress_then_closes(client: TestClient) -> None:
    job_id = client.post("/jobs", json={"kind": "echo", "payload": {"steps": 2}}).json()["id"]
    lines: list[str] = []
    with client.stream("GET", f"/jobs/{job_id}/events") as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        lines = list(r.iter_lines())
    events = [json.loads(line[6:]) for line in lines if line.startswith("data: ")]
    assert events[0] == {"progress": 50, "step": 1}
    assert events[1] == {"progress": 100, "step": 2}
    assert events[-1] == {"status": "done"}  # stream closes on the terminal event
