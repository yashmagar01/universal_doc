"""Ingestion API acceptance: upload -> job -> analysis (FR-ING-01/03, §11)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pymupdf
from fastapi.testclient import TestClient

from templix.model import SlotKind, Template

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "generated"


def _wait_done(client: TestClient, job_id: str, timeout_s: float = 60.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        body: dict[str, Any] = client.get(f"/api/v1/jobs/{job_id}").json()
        if body["status"] in ("done", "failed", "cancelled"):
            return body
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish")


def _upload(client: TestClient, fixture: str) -> dict[str, str]:
    with (FIXTURES / fixture).open("rb") as handle:
        response = client.post(
            "/api/v1/templates/ingest",
            files={"file": (fixture, handle, "application/pdf")},
        )
    assert response.status_code == 202, response.text
    body: dict[str, str] = response.json()
    assert body["jobId"] and body["templateId"]
    return body


def test_upload_ingest_analysis_roundtrip(client: TestClient) -> None:
    started = time.monotonic()
    ids = _upload(client, "newsletter_2col.pdf")
    job = _wait_done(client, ids["jobId"])
    assert job["status"] == "done", job
    assert time.monotonic() - started <= 10.0  # NFR-PERF-03: 2-page fixture in <= 10 s

    analysis = client.get(f"/api/v1/templates/{ids['templateId']}/analysis")
    assert analysis.status_code == 200
    body = analysis.json()
    assert 0.0 < body["confidence"] <= 1.0
    template = body["template"]
    assert len(template["pages"]) == 2
    assert template["slots"]
    assert template["reviewItems"]
    assert template["source"]["fileName"] == "newsletter_2col.pdf"

    listed = client.get("/api/v1/templates").json()
    row = next(r for r in listed if r["id"] == ids["templateId"])
    assert row["pageCount"] == 2
    assert row["layerCount"] > 0
    assert row["status"] == "needs-review"  # Helvetica alias warnings are expected on fixtures


def test_20_page_ingest_under_45s(client: TestClient, tmp_path: Path) -> None:
    """NFR-PERF-03 release gate: 20 pages reach template-ready in <= 45 s."""
    source = FIXTURES / "newsletter_2col.pdf"
    target = tmp_path / "newsletter_20page.pdf"
    src: Any = pymupdf.open(source)
    out: Any = pymupdf.open()
    with src, out:
        assert src.page_count == 2
        for _ in range(10):
            out.insert_pdf(src)
        out.save(target)

    started = time.monotonic()
    with target.open("rb") as handle:
        response = client.post(
            "/api/v1/templates/ingest",
            files={"file": (target.name, handle, "application/pdf")},
        )
    assert response.status_code == 202, response.text
    ids = response.json()
    job = _wait_done(client, ids["jobId"], timeout_s=50.0)
    elapsed = time.monotonic() - started
    assert job["status"] == "done", job
    assert elapsed <= 45.0, f"20-page ingest took {elapsed:.1f}s"

    analysis = client.get(f"/api/v1/templates/{ids['templateId']}/analysis").json()
    assert len(analysis["template"]["pages"]) == 20


def test_reference_raster_served(client: TestClient) -> None:
    ids = _upload(client, "report_6page.pdf")
    assert _wait_done(client, ids["jobId"])["status"] == "done"
    png = client.get(f"/api/v1/templates/{ids['templateId']}/pages/0/reference.png")
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.content.startswith(b"\x89PNG")
    assert client.get(f"/api/v1/templates/{ids['templateId']}/pages/9/reference.png").status_code == 404


def test_malformed_upload_fails_job(client: TestClient) -> None:
    ids = _upload(client, "malformed.pdf")
    job = _wait_done(client, ids["jobId"])
    assert job["status"] == "failed"
    assert job["error"].startswith("corrupt")


def test_non_pdf_rejected_before_job(client: TestClient) -> None:
    response = client.post(
        "/api/v1/templates/ingest",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "not_pdf"
    assert body["hint"]


def test_cancel_endpoint_on_finished_job_is_idempotent(client: TestClient) -> None:
    ids = _upload(client, "exec_weekly_1page.pdf")
    assert _wait_done(client, ids["jobId"])["status"] == "done"
    response = client.post(f"/api/v1/jobs/{ids['jobId']}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_edit_export_roundtrip(client: TestClient) -> None:
    """FR-EXP-01 interim: a changed slot is present at the original position in a real PDF."""
    ids = _upload(client, "newsletter_2col.pdf")
    assert _wait_done(client, ids["jobId"])["status"] == "done"
    analysis = client.get(f"/api/v1/templates/{ids['templateId']}/analysis").json()
    template = Template.model_validate(analysis["template"])
    nodes = {
        node.id: node
        for page in template.pages
        for group in page.nodes
        for node in group.children or []
    }
    slot = next(
        slot
        for slot in template.slots
        if slot.kind == SlotKind.text
        and len(slot.nodeIds) == 1
        and nodes[slot.nodeIds[0]].runs
    )
    original_node = nodes[slot.nodeIds[0]]
    original = "".join(run.text for run in original_node.runs or [])
    doc = client.post("/api/v1/documents", json={"templateId": ids["templateId"]}).json()
    assert "".join(run["text"] for run in doc["content"]["values"][slot.id]) == original

    replacement = "Templix export round trip"
    applied = client.post(
        f"/api/v1/documents/{doc['id']}/ops",
        json={"ops": [{"kind": "set_slot", "slotId": slot.id, "value": [{"text": replacement}]}]},
    )
    assert applied.status_code == 200

    response = client.get(f"/api/v1/documents/{doc['id']}/export.pdf")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "attachment" in response.headers["content-disposition"]

    pdf: Any = pymupdf.open(stream=response.content, filetype="pdf")
    try:
        text = "\n".join(page.get_text() for page in pdf)
        page_no = original_node.provenance.page if original_node.provenance else 0
        hits = pdf[page_no or 0].search_for(replacement)
        assert hits, "replacement text must be findable on the source page"
        # A y-flip or a style-less redraw moves the text; the frame must stay put.
        assert abs(hits[0].x0 - original_node.bbox.x) < 2
        assert abs(hits[0].y0 - original_node.bbox.y) < 6
    finally:
        pdf.close()
    assert replacement in text
    assert "Student Affairs Publication Office" in text


def test_export_rejects_text_that_cannot_fit(client: TestClient) -> None:
    """A too-long edit must fail loudly, not return a PDF with the text missing."""
    ids = _upload(client, "newsletter_2col.pdf")
    assert _wait_done(client, ids["jobId"])["status"] == "done"
    analysis = client.get(f"/api/v1/templates/{ids['templateId']}/analysis").json()
    template = Template.model_validate(analysis["template"])
    slot = next(
        slot
        for slot in template.slots
        if slot.kind == SlotKind.text and len(slot.nodeIds) == 1
    )
    doc = client.post("/api/v1/documents", json={"templateId": ids["templateId"]}).json()
    applied = client.post(
        f"/api/v1/documents/{doc['id']}/ops",
        json={"ops": [{"kind": "set_slot", "slotId": slot.id, "value": [{"text": "x" * 10_000}]}]},
    )
    assert applied.status_code == 200

    response = client.get(f"/api/v1/documents/{doc['id']}/export.pdf")
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "text_overflow"
