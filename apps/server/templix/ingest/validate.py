"""Upload validation that needs no parsing (FR-ING-01, stage 0a).

Magic bytes and size are checked at the API boundary so a hostile or wrong file is rejected
before anything touches disk. Encryption, page count and corruption need to open the PDF and
therefore run inside the sandboxed worker (stage 0b, `templix.ingest.native.probe`).
"""

from __future__ import annotations

from .errors import MAX_PDF_BYTES, IngestError

MAGIC = b"%PDF"


def check_upload(data: bytes) -> None:
    """Raise :class:`IngestError` for a non-PDF or oversized payload."""
    if len(data) > MAX_PDF_BYTES:
        raise IngestError("file_too_large")
    if not data.startswith(MAGIC):
        raise IngestError("not_pdf")
