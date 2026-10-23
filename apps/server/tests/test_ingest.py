"""Native extractor + sandbox acceptance (FR-ING-01/02/04, D-007 boundary, §6.2).

Ground truth for coverage is PyMuPDF's own `page.get_text()` stream: NFC-normalised
non-whitespace multiset, threshold 0.99 exactly as FR-ING-04 states. Measured value on every
healthy fixture is 1.000 — the only divergence ever seen is `\n` line separators.
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, cast

import pymupdf
import pytest

from templix.ingest.errors import MAX_PDF_BYTES, IngestError
from templix.ingest.native import PyMuPDFExtractor
from templix.ingest.sandbox import (  # pyright: ignore[reportPrivateUsage]
    Limits,
    _spawn_kwargs,  # pyright: ignore[reportPrivateUsage]
    _wait_for_exit,  # pyright: ignore[reportPrivateUsage]
    _windows_job,  # pyright: ignore[reportPrivateUsage]
    run_worker,
)
from templix.ingest.validate import check_upload

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "generated"
SERVER_ROOT = Path(__file__).resolve().parents[1]
MANIFEST: list[dict[str, Any]] = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
HEALTHY = [entry for entry in MANIFEST if "expectError" not in entry]


def _non_ws(text: str) -> Counter[str]:
    return Counter(ch for ch in unicodedata.normalize("NFC", text) if not ch.isspace())


def _extract(entry: dict[str, Any], out_dir: Path, dpi: int = 72) -> dict[str, Any]:
    result = PyMuPDFExtractor().extract(str(FIXTURES / str(entry["file"])), str(out_dir), dpi=dpi)
    assert result["ok"] is True, result
    return result


@pytest.mark.parametrize("entry", HEALTHY, ids=[str(e["file"]) for e in HEALTHY])
def test_probe_healthy(entry: dict[str, Any]) -> None:
    result = PyMuPDFExtractor().probe(str(FIXTURES / str(entry["file"])))
    assert result == {"ok": True, "pageCount": int(entry["pages"])}


@pytest.mark.parametrize("entry", MANIFEST, ids=[str(e["file"]) for e in MANIFEST])
def test_probe_reports_manifest_error(entry: dict[str, Any]) -> None:
    expected = entry.get("expectError")
    if expected is None:
        return
    result = PyMuPDFExtractor().probe(str(FIXTURES / str(entry["file"])))
    assert result == {"ok": False, "code": str(expected)}


def test_probe_enforces_page_limit() -> None:
    result = PyMuPDFExtractor().probe(str(FIXTURES / "report_6page.pdf"), max_pages=5)
    assert result == {"ok": False, "code": "too_many_pages"}


@pytest.mark.parametrize("entry", HEALTHY, ids=[str(e["file"]) for e in HEALTHY])
def test_char_coverage(entry: dict[str, Any], tmp_path: Path) -> None:
    """FR-ING-04: extracted characters cover >= 99% of the document text."""
    out = _extract(entry, tmp_path)
    doc: Any = pymupdf.open(str(FIXTURES / str(entry["file"])))
    expected: Counter[str] = Counter()
    actual: Counter[str] = Counter()
    try:
        assert len(out["pages"]) == int(entry["pages"])
        for index, page_out in enumerate(out["pages"]):
            page: Any = doc.load_page(index)
            text: str = page.get_text()
            expected.update(_non_ws(text))
            for span in page_out["spans"]:
                actual.update(_non_ws(str(span["text"])))
    finally:
        doc.close()
    total = sum(expected.values())
    assert total > 0, "fixture has no text to measure against"
    covered = sum((actual & expected).values())
    assert covered / total >= 0.99, f"coverage {covered / total:.4f} < 0.99"


def test_extract_writes_rasters_and_fonts(tmp_path: Path) -> None:
    out = _extract(HEALTHY[0], tmp_path)
    rasters = [str(name) for name in out["rasters"]]
    assert len(rasters) == int(out["pageCount"])
    for name in rasters:
        assert (tmp_path / name).stat().st_size > 0
    assert out["fonts"], "expected at least one font entry"


def test_image_dpi_measurements(tmp_path: Path) -> None:
    """image_page.pdf ships one 150 dpi and one 8 dpi image — the low-dpi rule has both cases."""
    entry = next(e for e in HEALTHY if e["file"] == "image_page.pdf")
    out = _extract(entry, tmp_path)
    dpis = [float(img["dpi"]) for page in out["pages"] for img in page["images"]]
    assert len(dpis) == 2, dpis
    assert max(dpis) >= 150
    assert min(dpis) < 150


def test_vectors_carry_path_data(tmp_path: Path) -> None:
    entry = next(e for e in HEALTHY if e["file"] == "newsletter_2col.pdf")
    out = _extract(entry, tmp_path)
    vectors = [v for page in out["pages"] for v in page["vectors"]]
    assert vectors, "newsletter should contain rules/borders"
    assert all(str(v["path"]) for v in vectors)


def test_sandbox_probe_roundtrip() -> None:
    result = run_worker("probe", str(FIXTURES / "newsletter_2col.pdf"))
    assert result["ok"] is True
    assert int(result["pageCount"]) == 2
    assert "elapsedS" in result


def test_sandbox_surfaces_worker_errors() -> None:
    malformed = run_worker("probe", str(FIXTURES / "malformed.pdf"))
    assert malformed["ok"] is False
    assert malformed["code"] == "corrupt"
    assert malformed["hint"]

    encrypted = run_worker("probe", str(FIXTURES / "encrypted.pdf"))
    assert encrypted["ok"] is False
    assert encrypted["code"] == "encrypted"


def test_sandbox_wall_clock_kills_worker(tmp_path: Path) -> None:
    limits = Limits(wall_clock_s=0.0001)
    result = run_worker(
        "extract",
        str(FIXTURES / "report_6page.pdf"),
        out_dir=str(tmp_path),
        limits=limits,
    )
    assert result["ok"] is False
    assert result["code"] == "timeout"


def test_sandbox_cancel_kills_running_child() -> None:
    cancel = threading.Event()
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    timer = threading.Timer(0.2, cancel.set)
    timer.start()
    started = time.monotonic()
    try:
        assert _wait_for_exit(proc, timeout_s=30.0, cancel=cancel) == "cancelled"
    finally:
        timer.cancel()
    assert time.monotonic() - started < 10


def test_sandbox_cancel_returns_cancelled(tmp_path: Path) -> None:
    cancel = threading.Event()
    cancel.set()
    result = run_worker(
        "extract",
        str(FIXTURES / "report_6page.pdf"),
        out_dir=str(tmp_path),
        limits=Limits(wall_clock_s=30.0),
        cancel=cancel,
    )
    assert result["code"] == "cancelled"
    assert result["ok"] is False


_ALLOCATOR = "import time; time.sleep(0.5); x = bytearray(128 * 1024 * 1024); print('allocated')"


def _run_allocator(limits: Limits | None) -> tuple[int, bytes, bytes]:
    kwargs: dict[str, Any] = _spawn_kwargs(limits) if limits is not None else {}
    proc = subprocess.Popen(
        [sys.executable, "-c", _ALLOCATOR],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )
    job = _windows_job(proc, limits) if limits is not None and os.name == "nt" else None
    try:
        out, err = proc.communicate(timeout=30)
    finally:
        if job is not None:
            ctypes.windll.kernel32.CloseHandle(job)  # pyright: ignore[reportAttributeAccessIssue]
    return proc.returncode, cast(bytes, out or b""), cast(bytes, err or b"")


def test_sandbox_memory_cap_is_enforced() -> None:
    """NFR-SEC-04: a child over the cap is stopped instead of consuming host memory."""
    control_rc, control_out, _ = _run_allocator(None)
    assert control_rc == 0, "control allocator failed without a cap"
    assert b"allocated" in control_out

    capped_rc, capped_out, capped_err = _run_allocator(Limits(wall_clock_s=10, memory_mb=64))
    assert capped_rc != 0
    assert b"allocated" not in capped_out
    assert b"MemoryError" in capped_err, capped_err


def test_pymupdf_stays_inside_native_boundary() -> None:
    """D-007: no module outside templix/ingest/native may import fitz/pymupdf."""
    offenders = [
        str(path.relative_to(SERVER_ROOT))
        for path in sorted((SERVER_ROOT / "templix").rglob("*.py"))
        if "native" not in path.relative_to(SERVER_ROOT).parts
        and re.search(r"^\s*(?:import|from)\s+(?:fitz|pymupdf)\b", path.read_text(encoding="utf-8"), re.M)
    ]
    assert offenders == []


def test_validate_rejects_non_pdf() -> None:
    with pytest.raises(IngestError) as excinfo:
        check_upload(b"not a pdf at all")
    assert excinfo.value.code == "not_pdf"


def test_validate_rejects_oversize() -> None:
    payload = b"%PDF" + b"\0" * MAX_PDF_BYTES
    with pytest.raises(IngestError) as excinfo:
        check_upload(payload)
    assert excinfo.value.code == "file_too_large"


def test_validate_accepts_pdf_magic() -> None:
    check_upload(b"%PDF-1.7 rest of the file")
