"""Sandbox worker entry: `python -m templix.ingest.native <in.json> <out.json>` (FR-ING-01, NFR-SEC-04).

Runs in a resource-limited subprocess (`templix.ingest.sandbox`). Contract:

- in.json:  {"mode": "probe"|"extract"|"export", "pdf": path, "outDir": path?, "dpi": int?, "maxPages": int?}
- out.json: {"ok": true, ...} or {"ok": false, "code": <ingest error code>, "hint": str}

No parent state, no network, no server imports — the parent treats this process as hostile
territory: wall-clock timeout, memory cap, output-size cap. Exit code 0 whenever out.json was
written (even for `ok: false`); a non-zero exit means the parent maps it to `limit`/`crash`.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any, cast

from templix.ingest.errors import HINTS, MAX_PDF_PAGES, IngestError


def _load(path: str) -> dict[str, Any]:
    payload: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    return cast(dict[str, Any], payload)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python -m templix.ingest.native <in.json> <out.json>", file=sys.stderr)
        return 2
    try:
        payload = _load(argv[1])
        from templix.ingest.native import PyMuPDFExtractor  # deferred: keeps `--help`-fast imports light

        extractor = PyMuPDFExtractor()
        mode = payload.get("mode")
        pdf = str(payload["pdf"])
        if mode == "probe":
            result = extractor.probe(pdf, int(payload.get("maxPages", 0)) or MAX_PDF_PAGES)
        elif mode == "extract":
            result = extractor.extract(pdf, str(payload["outDir"]), int(payload.get("dpi", 150)))
        elif mode == "export":
            from templix.ingest.native.export import export_document
            from templix.model import Document, Template

            result = export_document(
                Template.model_validate(payload["template"]),
                Document.model_validate(payload["document"]),
                pdf,
                str(payload["outPdf"]),
            )
        else:
            raise IngestError("crash", f"unknown mode {mode!r}")
    except IngestError as exc:
        result = {"ok": False, "code": exc.code, "hint": HINTS.get(exc.code, "")}
    except MemoryError:
        return 3  # no out.json: parent maps the exit to `limit`
    except Exception:
        traceback.print_exc()
        result = {"ok": False, "code": "corrupt", "hint": HINTS["corrupt"]}
    Path(argv[2]).write_text(json.dumps(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
