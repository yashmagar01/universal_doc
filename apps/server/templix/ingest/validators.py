"""Ingestion validators (FR-ING-13, architecture §6.4).

Four scans, each with a fixture that triggers it and one that does not:

- contrast: text vs the last filled vector covering >= 90 % of its box (else page white);
  WCAG thresholds 4.5:1 body / 3:1 large (>= 18 pt, or bold >= 14 pt);
- clipped: a node box sticking out of the page;
- overlap: text boxes overlapping by more than half the smaller area;
- imageDpi: raster below the 150 dpi minimum that slot constraint / imageMinDpi use.

Findings are plain `Detection`s without ids; the pipeline owns the kind-### numbering.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..model import Severity
from .errors import MIN_IMAGE_DPI
from .heuristics import PageLayout

LARGE_TEXT_PT = 18.0
LARGE_BOLD_PT = 14.0
COVER_FRACTION = 0.9
OVERLAP_FRACTION = 0.5
PAGE_TOLERANCE = 0.5


@dataclass
class TextProbe:
    node_id: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    color: str
    size: float
    bold: bool


@dataclass
class Detection:
    kind: str
    node_ids: list[str]
    severity: Severity
    suggestion: str
    confidence: float
    auto_fix: dict[str, object] | None = None


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    r = _linear(int(hex_color[1:3], 16) / 255)
    g = _linear(int(hex_color[3:5], 16) / 255)
    b = _linear(int(hex_color[5:7], 16) / 255)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    a, b = _luminance(fg), _luminance(bg)
    if a < b:
        a, b = b, a
    return (a + 0.05) / (b + 0.05)


def _area(box: tuple[float, float, float, float]) -> float:
    return max(box[2] - box[0], 0.0) * max(box[3] - box[1], 0.0)


def _background_for(probe: TextProbe, layout: PageLayout) -> str:
    text = (probe.x0, probe.y0, probe.x1, probe.y1)
    area = _area(text)
    background = "#FFFFFF"
    for shape in layout.shapes:  # painting order: the last covering fill wins
        if shape.fill is None:
            continue
        sx0 = max(text[0], shape.x0)
        sy0 = max(text[1], shape.y0)
        sx1 = min(text[2], shape.x1)
        sy1 = min(text[3], shape.y1)
        if area > 0 and _area((sx0, sy0, sx1, sy1)) >= COVER_FRACTION * area:
            background = shape.fill
    return background


def _needed_ratio(size: float, bold: bool) -> float:
    return 3.0 if size >= LARGE_TEXT_PT or (bold and size >= LARGE_BOLD_PT) else 4.5


def _contrast_findings(texts: list[TextProbe], layouts: dict[int, PageLayout]) -> list[Detection]:
    findings: list[Detection] = []
    for probe in texts:
        layout = layouts.get(probe.page)
        if layout is None:
            continue
        background = _background_for(probe, layout)
        ratio = contrast_ratio(probe.color, background)
        need = _needed_ratio(probe.size, probe.bold)
        if ratio < need:
            findings.append(
                Detection(
                    kind="contrast",
                    node_ids=[probe.node_id],
                    severity=Severity.warn,
                    suggestion=(
                        f"Contrast {ratio:.1f}:1 is below the {need:.1f}:1 minimum. "
                        "Darken the text or lighten its background."
                    ),
                    confidence=0.9,
                )
            )
    return findings


def _clipped_findings(texts: list[TextProbe], layouts: dict[int, PageLayout]) -> list[Detection]:
    findings: list[Detection] = []
    for probe in texts:
        layout = layouts.get(probe.page)
        if layout is None:
            continue
        out = (
            probe.x0 < -PAGE_TOLERANCE
            or probe.y0 < -PAGE_TOLERANCE
            or probe.x1 > layout.width + PAGE_TOLERANCE
            or probe.y1 > layout.height + PAGE_TOLERANCE
        )
        if out:
            findings.append(
                Detection(
                    kind="clipped",
                    node_ids=[probe.node_id],
                    severity=Severity.error,
                    suggestion="This text sits partly outside the page. Move or resize it.",
                    confidence=0.9,
                )
            )
    return findings


def _overlap_findings(texts: list[TextProbe]) -> list[Detection]:
    findings: list[Detection] = []
    by_page: dict[int, list[TextProbe]] = {}
    for probe in texts:
        by_page.setdefault(probe.page, []).append(probe)
    for page_texts in by_page.values():
        for i, a in enumerate(page_texts):
            for b in page_texts[i + 1 :]:
                inter = _area(
                    (max(a.x0, b.x0), max(a.y0, b.y0), min(a.x1, b.x1), min(a.y1, b.y1))
                )
                smaller = min(_area((a.x0, a.y0, a.x1, a.y1)), _area((b.x0, b.y0, b.x1, b.y1)))
                if smaller > 0 and inter > OVERLAP_FRACTION * smaller:
                    findings.append(
                        Detection(
                            kind="overlap",
                            node_ids=[a.node_id, b.node_id],
                            severity=Severity.warn,
                            suggestion="These text blocks overlap. Separate them or tighten their boxes.",
                            confidence=0.85,
                        )
                    )
    return findings


def _dpi_findings(layouts: dict[int, PageLayout], node_for_file: dict[str, str]) -> list[Detection]:
    findings: list[Detection] = []
    for layout in layouts.values():
        for figure in layout.figures:
            node_id = node_for_file.get(figure.file)
            if figure.dpi < MIN_IMAGE_DPI and node_id is not None:
                findings.append(
                    Detection(
                        kind="imageDpi",
                        node_ids=[node_id],
                        severity=Severity.warn,
                        suggestion=(
                            f"Image is {figure.dpi:.0f} dpi; the minimum is {MIN_IMAGE_DPI} dpi. "
                            "Replace it with a higher-resolution version."
                        ),
                        confidence=0.95,
                    )
                )
    return findings


def detect(
    texts: list[TextProbe], layouts: list[PageLayout], node_for_file: dict[str, str]
) -> list[Detection]:
    """All validator findings, ordered contrast -> clipped -> overlap -> imageDpi."""
    by_index = {layout.index: layout for layout in layouts}
    findings: list[Detection] = []
    findings.extend(_contrast_findings(texts, by_index))
    findings.extend(_clipped_findings(texts, by_index))
    findings.extend(_overlap_findings(texts))
    findings.extend(_dpi_findings(by_index, node_for_file))
    return findings
