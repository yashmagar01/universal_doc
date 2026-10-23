"""Heuristic layer (FR-ING-05/06/07, architecture §6.3 step 1).

Turns the raw extract dict into a ranked layout: text lines -> roles -> elements
(paragraph/heading segments, multi-column flows) plus figures and vector shapes.

Calibrated against the fixture corpus (see tests/test_heuristics.py for the exact
expected geometry per fixture):

- body size: character-weighted median of line sizes, bottom-zone lines excluded
  (footers/pagenumbers would drag a plain median down on sparse pages);
- lines join into elements when same role and y-pitch <= 2.5 x body size;
- body elements with two stable x0 clusters (range <= 2 pt, gap >= 24 pt) become
  2-column flows; ragged clusters (e.g. right-aligned amount columns) stay 1 column.

# ponytail: thresholds are constants, not config - the corpus is the contract. If a real
# document breaks a threshold the upgrade path is per-document re-clustering, not a settings UI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

TOP_ZONE = 0.15  # centre-line fraction of page height
BOTTOM_ZONE = 0.93
COLUMN_GAP_MIN = 24.0  # pt between x0 clusters to call it a column split
COLUMN_STABILITY = 2.0  # max x0 spread within one column, pt
JOIN_PITCH = 2.5  # x body size: max y-pitch that still merges into one element
CAPTION_REACH = 25.0  # pt around a figure/box for caption proximity
TALL_SHAPE = 30.0  # pt: shapes at least this tall can hold a caption
TITLE_FACTOR = 2.0
HEADING1_FACTOR = 1.4
HEADING2_FACTOR = 1.1
SMALL_FACTOR = 0.9  # running header/footer max size
TINY_FACTOR = 0.8  # caption max size

PAGENUM_RE = re.compile(r"page\s+\d+(\s+of\s+\d+)?", re.I)
BARE_NUM_RE = re.compile(r"\d{1,3}")
BYLINE_RE = re.compile(r"(by|written by|words by|story by|photos by|illustration by)\b", re.I)

ROLE_SCORE: dict[str, float] = {
    "title": 0.95,
    "pagenum": 0.95,
    "heading1": 0.9,
    "header": 0.85,
    "footer": 0.85,
    "byline": 0.85,
    "heading2": 0.8,
    "caption": 0.8,
    "quote": 0.8,
    "body": 0.75,
    "label": 0.7,
}


@dataclass
class Line:
    page: int
    block: int
    index: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    size: float
    bold: bool
    color: str
    font: str
    role: str = "body"

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


@dataclass
class Element:
    role: str
    lines: list[Line]
    columns: int = 1
    column_gap: float | None = None
    column_rule: bool = False

    @property
    def text(self) -> str:
        return "\n".join(line.text.rstrip() for line in self.lines)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (
            min(line.x0 for line in self.lines),
            min(line.y0 for line in self.lines),
            max(line.x1 for line in self.lines),
            max(line.y1 for line in self.lines),
        )

    @property
    def _dominant(self) -> Line:
        return max(self.lines, key=lambda line: line.width)

    @property
    def size(self) -> float:
        return self._dominant.size

    @property
    def bold(self) -> bool:
        return any(line.bold for line in self.lines)

    @property
    def color(self) -> str:
        return self._dominant.color

    @property
    def font(self) -> str:
        return self._dominant.font

    @property
    def leading(self) -> float:
        pitches = sorted(
            b.y0 - a.y0
            for a, b in zip(self.lines, self.lines[1:], strict=False)
            if b.y0 - a.y0 > 1.0
        )
        if not pitches:
            return round(1.3 * self.size, 1)
        return round(pitches[(len(pitches) - 1) // 2], 1)


@dataclass
class Figure:
    page: int
    file: str
    x0: float
    y0: float
    x1: float
    y1: float
    px_w: int
    px_h: int
    dpi: float
    mask: bool
    role: str = "photo"

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


@dataclass
class Shape:
    page: int
    role: str
    path: str
    fill: str | None
    stroke: str | None
    width: float
    dash: list[float]
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


@dataclass
class PageLayout:
    index: int
    width: float
    height: float
    elements: list[Element] = field(default_factory=list[Element])
    figures: list[Figure] = field(default_factory=list[Figure])
    shapes: list[Shape] = field(default_factory=list[Shape])


@dataclass
class Analysis:
    body_size: float
    baseline: float
    pages: list[PageLayout]


def _lines_for(page: dict[str, Any], number: int) -> list[Line]:
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for span in page["spans"]:
        grouped.setdefault((int(span["block"]), int(span["line"])), []).append(span)
    lines: list[Line] = []
    for (block, index), spans in grouped.items():
        widest = max(spans, key=lambda s: float(s["bbox"][2]) - float(s["bbox"][0]))
        lines.append(
            Line(
                page=number,
                block=block,
                index=index,
                text="".join(str(s["text"]) for s in spans),
                x0=min(float(s["bbox"][0]) for s in spans),
                y0=min(float(s["bbox"][1]) for s in spans),
                x1=max(float(s["bbox"][2]) for s in spans),
                y1=max(float(s["bbox"][3]) for s in spans),
                size=max(float(s["size"]) for s in spans),
                bold=any(int(s["flags"]) & 16 for s in spans),
                color=str(widest["color"]),
                font=str(widest["font"]),
            )
        )
    return sorted(lines, key=lambda ln: (ln.y0, ln.x0))


def _weighted_median(pairs: list[tuple[float, int]]) -> float:
    pairs = sorted(pairs)
    total = sum(weight for _, weight in pairs)
    if total == 0:
        return pairs[len(pairs) // 2][0]
    acc = 0
    for value, weight in pairs:
        acc += weight
        if acc * 2 >= total:
            return value
    return pairs[-1][0]


def _body_size(pages: list[dict[str, Any]], lines: list[Line]) -> float:
    heights = {int(p["index"]): float(p["height"]) for p in pages}
    pool = [
        (line.size, len(line.text))
        for line in lines
        if line.center_y < BOTTOM_ZONE * heights[line.page]
    ]
    if not pool:
        pool = [(line.size, len(line.text)) for line in lines]
    if not pool:
        return 10.0
    return _weighted_median(pool)


def _baseline(lines: list[Line], body_size: float) -> float:
    pitches: list[float] = []
    by_page: dict[int, list[Line]] = {}
    for line in lines:
        if line.role == "body":
            by_page.setdefault(line.page, []).append(line)
    for page_lines in by_page.values():
        page_lines.sort(key=lambda ln: (ln.y0, ln.x0))
        pitches.extend(
            round(b.y0 - a.y0, 1)
            for a, b in pairwise(page_lines)
            if 0.5 < b.y0 - a.y0 <= JOIN_PITCH * body_size
        )
    if not pitches:
        return round(1.3 * body_size, 1)
    pitches.sort()
    return pitches[(len(pitches) - 1) // 2]


def _near_figure(line: Line, boxes: list[tuple[float, float, float, float]]) -> bool:
    for x0, y0, x1, y1 in boxes:
        if line.x1 <= x0 or line.x0 >= x1:
            continue
        if line.y0 <= y1 + CAPTION_REACH and line.y1 >= y0 - CAPTION_REACH:
            return True
    return False


def _role_for(
    line: Line,
    body_size: float,
    page_height: float,
    caption_boxes: list[tuple[float, float, float, float]],
) -> str:
    text = line.text.strip()
    top = line.center_y <= TOP_ZONE * page_height
    bottom = line.center_y >= BOTTOM_ZONE * page_height
    if PAGENUM_RE.fullmatch(text) is not None and (top or bottom):
        return "pagenum"
    if BARE_NUM_RE.fullmatch(text) is not None and bottom:
        return "pagenum"
    if top and line.size <= round(SMALL_FACTOR * body_size, 3):
        return "header"
    if bottom and line.size <= round(SMALL_FACTOR * body_size, 3):
        return "footer"
    if line.size >= round(TITLE_FACTOR * body_size, 3):
        return "title"
    if line.size >= round(HEADING1_FACTOR * body_size, 3):
        return "heading1"
    if text.startswith("[") and text.endswith("]"):
        return "label"
    if line.size >= round(HEADING2_FACTOR * body_size, 3):
        return "heading2"
    if line.size <= round(TINY_FACTOR * body_size, 3) and _near_figure(line, caption_boxes):
        return "caption"
    if text.endswith(":") and len(text) <= 60:
        return "label"
    if BYLINE_RE.match(text) is not None:
        return "byline"
    if text[:1] in ("\u201c", '"', "'"):
        return "quote"
    return "body"


def _merge(lines: list[Line], body_size: float) -> list[Element]:
    """Chain same-role lines into elements.

    Same-row (y0 equal) appends only happen between *established* x0 columns (an x0 shared
    by >= 2 lines on the page) - that keeps two independent floats' captions apart while
    joining the two columns of a flow and the cells of a table row."""
    counts: dict[float, int] = {}
    for line in lines:
        key = round(line.x0, 1)
        counts[key] = counts.get(key, 0) + 1

    elements: list[Element] = []
    for line in sorted(lines, key=lambda ln: (ln.y0, ln.x0)):
        if not elements:
            elements.append(Element(role=line.role, lines=[line]))
            continue
        previous = elements[-1].lines[-1]
        # ponytail: labels are singleton annotations (bracket notes, colon labels); if a real
        # document ships a wrapped label this needs a size-compatibility check instead.
        joins = previous.role == line.role and line.role != "label"
        if joins:
            delta = line.y0 - previous.y0
            if delta <= 0.5:
                joins = (
                    counts.get(round(previous.x0, 1), 0) >= 2
                    and counts.get(round(line.x0, 1), 0) >= 2
                )
            else:
                joins = delta <= JOIN_PITCH * body_size
        if joins:
            elements[-1].lines.append(line)
        else:
            elements.append(Element(role=line.role, lines=[line]))
    return elements


def _column_rule_present(
    element: Element, shapes: list[dict[str, Any]], split: float, left_x1: float
) -> bool:
    height = element.bbox[3] - element.bbox[1]
    for vector in shapes:
        bbox = vector["bbox"]
        w = float(bbox[2]) - float(bbox[0])
        h = float(bbox[3]) - float(bbox[1])
        centre = (float(bbox[0]) + float(bbox[2])) / 2
        if w <= 3.0 and left_x1 - 2.0 <= centre <= split + 2.0 and h >= 0.6 * height:
            return True
    return False


def _detect_columns(element: Element, shapes: list[dict[str, Any]]) -> None:
    xs = sorted({round(line.x0, 1) for line in element.lines})
    if len(xs) < 2:
        return
    gap, split = max((b - a, b) for a, b in pairwise(xs))
    if gap < COLUMN_GAP_MIN:
        return
    left = [line for line in element.lines if line.x0 < split - 0.05]
    right = [line for line in element.lines if line.x0 >= split - 0.05]
    for cluster in (left, right):
        if len(cluster) < 2:
            return
        spread = max(line.x0 for line in cluster) - min(line.x0 for line in cluster)
        if spread > COLUMN_STABILITY:
            return
    column_gap = min(line.x0 for line in right) - max(line.x1 for line in left)
    left_x1 = max(line.x1 for line in left)
    element.lines = sorted(left, key=lambda ln: ln.y0) + sorted(right, key=lambda ln: ln.y0)
    element.columns = 2
    element.column_gap = round(column_gap, 1)
    element.column_rule = _column_rule_present(element, shapes, split, left_x1)


def _figures_for(page: dict[str, Any], number: int) -> list[Figure]:
    return [
        Figure(
            page=number,
            file=str(img["file"]),
            x0=float(img["bbox"][0]),
            y0=float(img["bbox"][1]),
            x1=float(img["bbox"][2]),
            y1=float(img["bbox"][3]),
            px_w=int(img["w"]),
            px_h=int(img["h"]),
            dpi=float(img["dpi"]),
            mask=bool(img.get("mask")),
        )
        for img in page["images"]
    ]


def _shapes_for(page: dict[str, Any], number: int) -> list[Shape]:
    shapes: list[Shape] = []
    for vector in page["vectors"]:
        bbox = vector["bbox"]
        x0, y0, x1, y1 = (float(v) for v in bbox)
        role = "rule" if (y1 - y0 <= 3.0 or x1 - x0 <= 3.0) else "box"
        shapes.append(
            Shape(
                page=number,
                role=role,
                path=str(vector["path"]),
                fill=vector.get("fill"),
                stroke=vector.get("stroke"),
                width=float(vector["width"]),
                dash=[float(d) for d in vector["dash"]],
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
            )
        )
    return shapes


def _assign_figure_roles(
    figures: list[Figure], elements: list[Element], layout_w: float, layout_h: float
) -> None:
    captions = [el for el in elements if el.role == "caption"]
    for figure in figures:
        area = (figure.x1 - figure.x0) * (figure.y1 - figure.y0)
        centre_y = (figure.y0 + figure.y1) / 2
        if area >= 0.95 * layout_w * layout_h:
            figure.role = "background"
        elif centre_y <= TOP_ZONE * layout_h:
            figure.role = "logo"
        elif any(
            caption.bbox[0] < figure.x1
            and caption.bbox[2] > figure.x0
            and figure.y1 - CAPTION_REACH <= caption.bbox[1] <= figure.y1 + CAPTION_REACH
            for caption in captions
        ):
            figure.role = "figure"
        else:
            figure.role = "photo"


def analyse(extract: dict[str, Any]) -> Analysis:
    """Full heuristic pass over one extract result (all pages)."""
    pages: list[dict[str, Any]] = extract["pages"]
    per_page_lines = [_lines_for(page, int(page["index"])) for page in pages]
    all_lines = [line for lines in per_page_lines for line in lines]
    body_size = _body_size(pages, all_lines)
    for page, lines in zip(pages, per_page_lines, strict=False):
        height = float(page["height"])
        caption_boxes = [
            (float(img["bbox"][0]), float(img["bbox"][1]), float(img["bbox"][2]), float(img["bbox"][3]))
            for img in page["images"]
        ] + [
            (float(v["bbox"][0]), float(v["bbox"][1]), float(v["bbox"][2]), float(v["bbox"][3]))
            for v in page["vectors"]
            if float(v["bbox"][3]) - float(v["bbox"][1]) >= TALL_SHAPE
        ]
        for line in lines:
            line.role = _role_for(line, body_size, height, caption_boxes)
    baseline = _baseline(all_lines, body_size)
    layouts: list[PageLayout] = []
    for page, lines in zip(pages, per_page_lines, strict=False):
        width, height = float(page["width"]), float(page["height"])
        vectors: list[dict[str, Any]] = page["vectors"]
        elements = _merge(lines, body_size)
        for element in elements:
            if element.role == "body":
                _detect_columns(element, vectors)
        figures = _figures_for(page, int(page["index"]))
        _assign_figure_roles(figures, elements, width, height)
        layouts.append(
            PageLayout(
                index=int(page["index"]),
                width=width,
                height=height,
                elements=elements,
                figures=figures,
                shapes=_shapes_for(page, int(page["index"])),
            )
        )
    return Analysis(body_size=round(body_size, 3), baseline=baseline, pages=layouts)
