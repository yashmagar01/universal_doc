"""Native extraction port (FR-ING-04, architecture §6.2, D-007).

`NativeExtractor` is the seam that keeps PyMuPDF replaceable (pypdfium2 if OQ-1 rejects AGPL):
the sandbox worker and the pipeline only ever speak this protocol's shapes. Every `fitz`/`pymupdf`
import in Templix lives inside this package — `tests/test_ingest.py` enforces that.

Shapes (plain serialisable dicts; unit = PDF points, top-left origin, y down — PyMuPDF already
speaks that convention, so no transform is needed at this boundary):

- probe  -> {"ok": True, "pageCount": int}                       | {"ok": False, "code": ...}
- extract -> {"ok": True, "pageCount", "pages": [NativePage], "fonts": {name: FontInfo},
              "rasters": [file names], "images": [ImageRef]}
"""

from __future__ import annotations

from typing import Any, Protocol

from ..errors import MAX_PDF_PAGES
from .pymupdf_native import PyMuPDFExtractor


class NativeExtractor(Protocol):
    """What the pipeline needs from a PDF engine (FR-ING-01/02/04)."""

    def probe(self, pdf_path: str, max_pages: int = MAX_PDF_PAGES) -> dict[str, Any]:
        """Validate without extracting: encrypted / corrupt / page count."""
        ...

    def extract(self, pdf_path: str, out_dir: str, dpi: int = 150) -> dict[str, Any]:
        """Full native pass: spans, images, vectors, page boxes + reference rasters + image assets."""
        ...


def default_extractor() -> PyMuPDFExtractor:
    return PyMuPDFExtractor()


__all__ = ["NativeExtractor", "PyMuPDFExtractor", "default_extractor"]
