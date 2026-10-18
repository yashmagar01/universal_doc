"""Ingestion failure codes (FR-ING-01/02): one distinct code + human hint per failure mode.

The upload endpoint returns `{code, hint}` for what it can check without parsing (magic bytes,
size); everything that needs to open the PDF fails the job with the same code/hint pair so the
client only ever learns one vocabulary.
"""

from __future__ import annotations

MAX_PDF_BYTES = 50 * 1024 * 1024  # FR-ING-01
MAX_PDF_PAGES = 50  # FR-ING-01 soft limit (override at upload)
MIN_IMAGE_DPI = 150  # architecture §6.4 validators / imageMinDpi rule

HINTS: dict[str, str] = {
    "not_pdf": "This file does not start with a %PDF header. Export it as PDF and upload it again.",
    "file_too_large": "The file is larger than the 50 MB upload limit. Split it or export a smaller PDF.",
    "encrypted": "This PDF is password protected. Remove the password, export it again, and re-upload.",
    "corrupt": "This PDF could not be parsed. Re-export it from the source application and try again.",
    "too_many_pages": "This PDF has more than 50 pages. Turn on the page-limit override to ingest it anyway.",
    "timeout": "Parsing exceeded the wall-clock limit and was stopped before it could finish.",
    "limit": "Parsing exceeded its CPU or memory limits and was stopped. Try a smaller document.",
    "crash": "The parser crashed. The server stayed up; try re-exporting the file.",
}


class IngestError(Exception):
    """A coded ingestion failure: `str(exc)` is ``"code: hint"`` for job records and logs."""

    def __init__(self, code: str, hint: str | None = None) -> None:
        self.code = code
        self.hint = hint or HINTS.get(code, code)
        super().__init__(f"{self.code}: {self.hint}")
