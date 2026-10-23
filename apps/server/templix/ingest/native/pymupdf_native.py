# ponytail: pymupdf ships partial type info; unknown-typed members are silenced HERE only (D-007
# boundary), strict mode stays on for every other module. Revisit if pypdfium2 wins OQ-1.
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportCallIssue=false, reportArgumentType=false, reportUnnecessaryComparison=false
"""PyMuPDF implementation of `NativeExtractor` (FR-ING-04, architecture §6.2).

**D-007 boundary:** this is the only module in Templix that imports `fitz`/`pymupdf`. The sandbox
runs `python -m templix.ingest.native` so a crashing PDF parser never takes the server with it.

Coordinate convention: PyMuPDF already reports top-left origin / y down (§5.2), so bboxes pass
through unchanged; units are PDF points. Colours: spans are sRGB ints, drawings are 0-1 floats -
both normalise to `#RRGGBB` here so the rest of the system only sees one colour format.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pymupdf as fitz

from ..errors import MAX_PDF_PAGES

_SUBSET_RE = re.compile(r"^[A-Z]{6}\+")


def _int_color(value: int) -> str:
    """PyMuPDF span colour (packed sRGB int) -> `#RRGGBB`."""
    return f"#{value & 0xFFFFFF:06X}"


def _float_color(value: tuple[float, ...] | None) -> str | None:
    """Drawing colour (0-1 floats) -> `#RRGGBB`."""
    if value is None or len(value) < 3:
        return None
    r, g, b = (max(0.0, min(1.0, c)) for c in value[:3])
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def _pt(p: Any) -> list[float]:
    return [round(float(p.x), 3), round(float(p.y), 3)]


def _rect(r: Any) -> list[float]:
    return [round(float(r.x0), 3), round(float(r.y0), 3), round(float(r.x1), 3), round(float(r.y1), 3)]


def _path_data(items: list[Any]) -> str:
    """Drawing items -> SVG path data. Rects/lines collapse to path primitives (§6.2)."""
    parts: list[str] = []
    current: tuple[float, float] | None = None
    for item in items:
        kind = item[0]
        if kind == "l":  # lineTo
            p1, p2 = item[1], item[2]
            if current is None or current != (p1.x, p1.y):
                parts.append(f"M{_pt(p1)[0]} {_pt(p1)[1]}")
            parts.append(f"L{_pt(p2)[0]} {_pt(p2)[1]}")
            current = (p2.x, p2.y)
        elif kind == "c":  # cubic Bézier: (start, ctrl1, ctrl2, end)
            p1, p2, p3, p4 = item[1], item[2], item[3], item[4]
            if current is None or current != (p1.x, p1.y):
                parts.append(f"M{_pt(p1)[0]} {_pt(p1)[1]}")
            parts.append(
                f"C{_pt(p2)[0]} {_pt(p2)[1]} {_pt(p3)[0]} {_pt(p3)[1]} {_pt(p4)[0]} {_pt(p4)[1]}"
            )
            current = (p4.x, p4.y)
        elif kind == "re":  # rectangle primitive
            r = item[1]
            x0, y0, x1, y1 = float(r.x0), float(r.y0), float(r.x1), float(r.y1)
            parts.append(f"M{x0:.3f} {y0:.3f}L{x1:.3f} {y0:.3f}L{x1:.3f} {y1:.3f}L{x0:.3f} {y1:.3f}Z")
            current = (x0, y0)
        elif kind == "qu":  # quad
            q = item[1]
            pts = [(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y)]
            parts.append("M" + f"{pts[0][0]:.3f} {pts[0][1]:.3f}" + "".join(
                f"L{x:.3f} {y:.3f}" for x, y in pts[1:]
            ) + "Z")
            current = pts[0]
    return "".join(parts)


class PyMuPDFExtractor:
    """`NativeExtractor` backed by PyMuPDF (AGPL — see docs/licensing.md)."""

    def probe(self, pdf_path: str, max_pages: int = MAX_PDF_PAGES) -> dict[str, Any]:
        """Stage 0b validation (FR-ING-01): open, page count, encryption — no extraction."""
        try:
            doc = fitz.open(pdf_path)
        except Exception:
            return {"ok": False, "code": "corrupt"}
        try:
            if doc.needs_pass:
                return {"ok": False, "code": "encrypted"}
            count = doc.page_count
            if count < 1:
                return {"ok": False, "code": "corrupt"}
            # force-parse every page so structural damage fails here, not mid-extraction
            for i in range(count):
                doc.load_page(i)
            if count > max_pages:
                return {"ok": False, "code": "too_many_pages"}
        except Exception:
            return {"ok": False, "code": "corrupt"}
        finally:
            doc.close()
        return {"ok": True, "pageCount": count}

    def extract(self, pdf_path: str, out_dir: str, dpi: int = 150) -> dict[str, Any]:
        """Full native pass (§6.2): spans, images, vectors, page boxes, fonts, rasters, assets."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(pdf_path)
        pages: list[dict[str, Any]] = []
        fonts: dict[str, dict[str, Any]] = {}
        images: list[dict[str, Any]] = []
        rasters: list[str] = []
        try:
            for pno in range(doc.page_count):
                page = doc.load_page(pno)
                spans: list[dict[str, Any]] = []
                raw = page.get_text("dict")
                for bi, block in enumerate(raw["blocks"]):
                    if block["type"] != 0:
                        continue
                    for li, line in enumerate(block["lines"]):
                        for span in line["spans"]:
                            if not span["text"]:
                                continue
                            spans.append(
                                {
                                    "text": span["text"],
                                    "font": span["font"],
                                    "size": round(float(span["size"]), 3),
                                    "flags": int(span["flags"]),
                                    "color": _int_color(int(span["color"])),
                                    "bbox": [round(v, 3) for v in span["bbox"]],
                                    "origin": [round(span["origin"][0], 3), round(span["origin"][1], 3)],
                                    "block": bi,
                                    "line": li,
                                }
                            )

                page_images: list[dict[str, Any]] = []
                for info in page.get_image_info(xrefs=True):
                    xref = int(info.get("xref") or 0)
                    if xref <= 0:
                        continue  # inline image: no reusable asset (flagged as review if referenced)
                    try:
                        extracted = doc.extract_image(xref)
                    except Exception:
                        continue
                    ext = str(extracted.get("ext", "png"))
                    fname = f"img-{len(images)}.{ext}"
                    (out / fname).write_bytes(extracted["image"])
                    bbox = [round(v, 3) for v in info["bbox"]]
                    w_pt = max(bbox[2] - bbox[0], 0.01)
                    h_pt = max(bbox[3] - bbox[1], 0.01)
                    w_px, h_px = int(info["width"]), int(info["height"])
                    page_images.append(
                        {
                            "file": fname,
                            "bbox": bbox,
                            "w": w_px,
                            "h": h_px,
                            "dpi": round(max(w_px / (w_pt / 72.0), h_px / (h_pt / 72.0)), 1),
                            "xref": xref,
                            "mask": bool(info.get("has-mask")),
                        }
                    )
                    images.append({"file": fname, "xref": xref})

                vectors: list[dict[str, Any]] = []
                for d in page.get_drawings():
                    scissor = d.get("scissor")
                    vectors.append(
                        {
                            "paint": d.get("type", "f"),
                            "fill": _float_color(d.get("fill")),
                            "stroke": _float_color(d.get("color")),  # PyMuPDF names stroke colour `color`
                            "width": round(float(d.get("width") or 0.0), 3),
                            "dash": [float(x) for x in (d.get("dashes") or "").strip("[]").split()]
                            if d.get("dashes") not in (None, "[] 0")
                            else [],
                            "opacity": d.get("fill_opacity", d.get("opacity")),
                            "bbox": _rect(d["rect"]),
                            "clip": _rect(scissor["rect"]) if isinstance(scissor, dict) else None,
                            "path": _path_data(d["items"]),
                        }
                    )

                links = [
                    {"bbox": _rect(link["from"]), "uri": link.get("uri") or ""}
                    for link in page.get_links()
                    if link.get("kind") in (fitz.LINK_URI, fitz.LINK_GOTO) and link.get("from")
                ]

                for xref, ext, ftype, basefont, _fullname, _enc in doc.get_page_fonts(pno):
                    name = str(basefont)
                    # `ext` "" / "n/a" means no font file ships with the PDF (base-14 like Helvetica)
                    file_backed = str(ext) not in ("", "n/a")
                    entry = fonts.setdefault(
                        name,
                        {
                            "subset": bool(_SUBSET_RE.match(name)),
                            "embedded": bool(xref) and file_backed,
                            "type": str(ftype),
                            "ext": str(ext),
                        },
                    )
                    entry["embedded"] = entry["embedded"] or (bool(xref) and file_backed)

                raster = f"page-{pno}.png"
                page.get_pixmap(dpi=dpi).save(out / raster)
                rasters.append(raster)

                pages.append(
                    {
                        "index": pno,
                        "width": round(float(page.rect.width), 3),
                        "height": round(float(page.rect.height), 3),
                        "rotation": int(page.rotation),
                        "spans": spans,
                        "images": page_images,
                        "vectors": vectors,
                        "links": links,
                    }
                )
        finally:
            doc.close()
        return {"ok": True, "pageCount": len(pages), "pages": pages, "fonts": fonts, "rasters": rasters}
