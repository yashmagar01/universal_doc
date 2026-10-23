# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportCallIssue=false, reportArgumentType=false, reportUnnecessaryComparison=false, reportAttributeAccessIssue=false
"""Content-only PDF export (FR-EXP-01 interim, D-007 boundary).

The source PDF is the layout master. For every slot whose text changed, the original
text rectangle is redacted and the new text is drawn in the same frame. Everything else
(images, rules, untouched text) stays byte-for-byte in the source page. This is deliberately
not the M3 renderer: it makes manual text edits exportable today without pretending that
font fitting, reflow or image replacement are finished.

# shortcut: body text is split across the node's columns by line/word count, not by measured
# line breaking; upgrade to render-core DOM + Playwright when M3 lands. Rotated pages use the
# same top-left transform as upright pages; add a rotation fixture before claiming support.
"""

from __future__ import annotations

from collections.abc import Iterator
from math import ceil
from pathlib import Path
from typing import Any

import pymupdf as fitz

from ...model import Document, Node, Run, Slot, SlotKind, Template, TextStyle

_ALIGN = {"left": 0, "center": 1, "right": 2, "justify": 3}
_FONT_BOLD = {"helv": "hebo", "tiro": "tibo", "cour": "cobo"}


def _walk(nodes: list[Node]) -> Iterator[Node]:
    for node in nodes:
        yield node
        if node.children:
            yield from _walk(node.children)


def _text(runs: list[Run] | None) -> str:
    return "".join(run.text for run in runs or [])


def _node_index(template: Template) -> dict[str, tuple[int, Node]]:
    index: dict[str, tuple[int, Node]] = {}
    for page_no, page in enumerate(template.pages):
        for node in _walk(page.nodes):
            index[node.id] = (page_no, node)
    return index


def _original_text(slot: Slot, index: dict[str, tuple[int, Node]]) -> str:
    for node_id in slot.nodeIds:
        hit = index.get(node_id)
        if hit is not None and hit[1].runs:
            return _text(hit[1].runs)
    return ""


def _style(template: Template, node: Node) -> TextStyle | None:
    return template.tokens.textStyles.get(node.styleRef) if node.styleRef else None


def _font_name(template: Template, style: TextStyle | None) -> str:
    definition = template.tokens.fonts.get(style.font) if style else None
    family = (definition.family if definition else "").lower()
    bold = bool(definition and any(weight >= 600 for weight in definition.weights))
    if style is not None and style.font == "display":
        bold = True
    if "courier" in family or "mono" in family:
        base = "cour"
    elif any(token in family for token in ("times", "serif", "georgia", "garamond")):
        base = "tiro"
    else:
        base = "helv"
    return _FONT_BOLD[base] if bold else base


def _rgb(value: str | None, colors: dict[str, str]) -> tuple[float, float, float]:
    raw = colors.get(value, value) if value else "#000000"
    if raw is None or not raw.startswith("#") or len(raw) < 7:
        return (0.0, 0.0, 0.0)
    try:
        return tuple(int(raw[i : i + 2], 16) / 255 for i in (1, 3, 5))  # type: ignore[return-value]
    except ValueError:
        return (0.0, 0.0, 0.0)


def _pdf_rect(node: Node) -> Any:
    # PyMuPDF page coordinates are already top-left origin / y down (same as the template).
    return fitz.Rect(
        node.bbox.x,
        node.bbox.y,
        node.bbox.x + node.bbox.w,
        node.bbox.y + node.bbox.h,
    )


def _column_rects(rect: Any, count: int, gap: float) -> list[Any]:
    if count <= 1:
        return [rect]
    width = max((rect.width - gap * (count - 1)) / count, 1.0)
    return [
        fitz.Rect(
            rect.x0 + index * (width + gap),
            rect.y0,
            rect.x0 + index * (width + gap) + width,
            rect.y1,
        )
        for index in range(count)
    ]


def _chunks(text: str, count: int) -> list[str]:
    """Split into roughly equal column chunks; exact reflow is M3's job."""
    if count <= 1:
        return [text]
    lines = text.splitlines()
    if len(lines) >= count:
        per = ceil(len(lines) / count)
        chunks = ["\n".join(lines[index * per : (index + 1) * per]) for index in range(count)]
    else:
        words = text.split()
        chunks = []
        current: list[str] = []
        target = max(1, len(words) / count)
        for word in words:
            current.append(word)
            if len(chunks) < count - 1 and len(current) >= target:
                chunks.append(" ".join(current))
                current = []
        chunks.append(" ".join(current))
    while len(chunks) < count:
        chunks.append("")
    return chunks


def _draw_text(
    page: Any,
    rect: Any,
    text: str,
    style: TextStyle | None,
    font: str,
    color: tuple[float, float, float],
    align: int,
    columns: int,
    gap: float,
) -> bool:
    if not text.strip():
        return True
    size = max(style.size if style else 10.0, 1.0)
    leading = max(style.leading if style else size * 1.2, size)
    lineheight = max(0.8, min(2.0, leading / size))
    columns = max(columns, 1)
    for chunk, column in zip(_chunks(text, columns), _column_rects(rect, columns, gap), strict=False):
        if not chunk.strip():
            continue
        trial = size
        placed = False
        while trial >= 6.0:
            try:
                if page.insert_textbox(
                    column,
                    chunk,
                    fontsize=trial,
                    fontname=font,
                    color=color,
                    align=align,
                    lineheight=lineheight,
                ) >= 0:
                    placed = True
                    break
            except Exception:
                break
            trial -= 0.5
        if not placed:
            try:
                if (
                    page.insert_textbox(
                        column,
                        chunk,
                        fontsize=6.0,
                        fontname=font,
                        color=color,
                        align=align,
                        lineheight=lineheight,
                    )
                    < 0
                ):
                    return False
            except Exception:
                return False
    return True


def export_document(
    template: Template,
    document: Document,
    pdf_path: str,
    out_path: str,
) -> dict[str, Any]:
    """Write `out_path` with changed slot text replaced; return a small result dict."""
    index = _node_index(template)
    edits: dict[int, list[tuple[Any, str, Node]]] = {}
    edited_slots = 0
    pdf = fitz.open(pdf_path)

    try:
        for slot in template.slots:
            if slot.kind == SlotKind.image:
                continue
            runs = document.content.values.get(slot.id)
            # An absent value is untouched; an empty list is a pre-prefill document, not a clear.
            # The editor clears a slot with one empty Run, which is a real redaction.
            if runs is None or runs == []:
                continue
            text = _text(runs)
            if text == _original_text(slot, index):
                continue
            touched = False
            for node_id in slot.nodeIds:
                hit = index.get(node_id)
                if hit is None:
                    continue
                page_no, node = hit
                if page_no < 0 or page_no >= pdf.page_count:
                    continue
                edits.setdefault(page_no, []).append((_pdf_rect(node), text, node))
                touched = True
            if touched:
                edited_slots += 1

        warnings: list[str] = []
        for page_no, page_edits in edits.items():
            page = pdf.load_page(page_no)
            for rect, _text_value, _node in page_edits:
                page.add_redact_annot(rect, fill=False)
            # Keep photos and rules under the text; only the glyphs are removed.
            page.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_NONE,
            )
            for rect, text, node in page_edits:
                style = _style(template, node)
                if not _draw_text(
                    page,
                    rect,
                    text,
                    style,
                    _font_name(template, style),
                    _rgb(style.color if style else None, template.tokens.colors),
                    _ALIGN.get(node.align or "left", 0),
                    node.columns or 1,
                    node.columnGap or 0.0,
                ):
                    warnings.append(f"page {page_no + 1}: could not place edited text")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        pdf.save(out_path, garbage=3, deflate=True)
    finally:
        pdf.close()

    return {"ok": True, "editedSlots": edited_slots, "warnings": warnings}
