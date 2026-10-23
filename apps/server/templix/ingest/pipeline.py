"""Ingestion pipeline (architecture §6.3): extract dict -> Template.

Wires the units together: heuristics (roles/elements/columns) -> tokens (palette, styles,
spacing) -> font cascade -> node/page assembly -> slots -> validators -> review items.
One group node per page (`role="section"`), document order children sorted by (y0, x0).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..model import (
    BBox,
    Fit,
    FitMode,
    FontResolution,
    FontSource,
    Node,
    NodeType,
    Page,
    Provenance,
    ReviewItem,
    Run,
    Severity,
    Size,
    Source,
    Template,
    new_ulid,
)
from ..store import BlobStore
from . import fonts, heuristics, validators
from .errors import MIN_IMAGE_DPI
from .heuristics import ROLE_SCORE, Analysis, Element
from .slots import SlotSource, build_slots
from .tokens import StyleBook, build_palette

IMAGE_SCORE = 0.9
SHAPE_SCORE = 0.9


def _geom(bbox: tuple[float, float, float, float], width: float, height: float) -> float:
    x0, y0, x1, y1 = bbox
    inside = x0 >= -0.5 and y0 >= -0.5 and x1 <= width + 0.5 and y1 <= height + 0.5
    return 1.0 if inside else 0.5


def _box(bbox: tuple[float, float, float, float]) -> BBox:
    return BBox(x=bbox[0], y=bbox[1], w=bbox[2] - bbox[0], h=bbox[3] - bbox[1])


def _text_node(
    element: Element,
    page_index: int,
    width: float,
    height: float,
    z: int,
    book: StyleBook,
    resolution: FontResolution,
) -> Node:
    role = element.role
    family = resolution.resolved or fonts.family_of(resolution.requested)
    style_ref = book.style_ref(
        role,
        size=element.size,
        leading=element.leading,
        color_hex=element.color,
        bold=element.bold,
        family=family,
        source=resolution.source or FontSource.system,
    )
    flow = role == "body"
    lines = len(element.lines)
    return Node(
        id=new_ulid(),
        type=NodeType.flow if flow else NodeType.text,
        role=role,
        bbox=_box(element.bbox),
        z=z,
        editable=role != "pagenum",
        confidence=min(ROLE_SCORE.get(role, 0.75), _geom(element.bbox, width, height)),
        provenance=Provenance(page=page_index, engine="native"),
        styleRef=style_ref,
        runs=[Run(text=element.text)],
        fit=Fit(mode="reflow", maxLines=lines)
        if flow
        else Fit(mode="shrink", minScale=0.9, maxLines=lines),
        columns=element.columns if flow else None,
        columnGap=element.column_gap if flow else None,
        columnRule=element.column_rule if flow else None,
        fontResolution=resolution,
    )


def build_template(
    extract: dict[str, Any],
    *,
    template_id: str,
    name: str,
    file_name: str,
    sha256: str,
    blob: BlobStore,
    out_dir: Path,
) -> Template:
    """Assemble a fully-populated Template from one successful extract."""
    analysis = heuristics.analyse(extract)
    book = StyleBook(build_palette(extract))
    resolutions = fonts.resolve_names(_font_names(analysis))

    pages: list[Page] = []
    slot_sources: list[SlotSource] = []
    probes: list[validators.TextProbe] = []
    node_for_file: dict[str, str] = {}
    by_font: dict[str, list[str]] = {}

    for layout in analysis.pages:
        children: list[Node] = []
        raster = f"page-{layout.index}.png"
        raster_path = out_dir / raster
        reference_sha = blob.put(raster_path.read_bytes()) if raster_path.exists() else None
        for element in layout.elements:
            resolution = resolutions[element.font]
            node = _text_node(
                element, layout.index, layout.width, layout.height, 0, book, resolution
            )
            children.append(node)
            by_font.setdefault(element.font, []).append(node.id)
            probes.append(
                validators.TextProbe(
                    node_id=node.id,
                    page=layout.index,
                    x0=element.bbox[0],
                    y0=element.bbox[1],
                    x1=element.bbox[2],
                    y1=element.bbox[3],
                    color=element.color,
                    size=element.size,
                    bold=element.bold,
                )
            )
            if element.role != "pagenum":
                slot_sources.append(
                    SlotSource(
                        node_id=node.id,
                        page=layout.index,
                        role=element.role,
                        text=element.text,
                        max_lines=len(element.lines),
                        fit="reflow" if element.role == "body" else "shrink",
                    )
                )
        for figure in layout.figures:
            asset_id = blob.put((out_dir / figure.file).read_bytes())
            node = Node(
                id=new_ulid(),
                type=NodeType.image,
                role=figure.role,
                bbox=_box(figure.bbox),
                editable=True,
                confidence=min(IMAGE_SCORE, _geom(figure.bbox, layout.width, layout.height)),
                provenance=Provenance(page=layout.index, engine="native"),
                assetId=asset_id,
                fitMode=FitMode.contain,
                aspectLock=True,
                minDpi=MIN_IMAGE_DPI,
            )
            children.append(node)
            node_for_file[figure.file] = node.id
            slot_sources.append(
                SlotSource(
                    node_id=node.id,
                    page=layout.index,
                    role=figure.role,
                    text="",
                    max_lines=1,
                    fit="contain",
                    kind="image",
                    min_dpi=MIN_IMAGE_DPI,
                )
            )
        for shape in layout.shapes:
            children.append(
                Node(
                    id=new_ulid(),
                    type=NodeType.shape,
                    role=shape.role,
                    bbox=_box(shape.bbox),
                    editable=False,
                    confidence=min(
                        SHAPE_SCORE, _geom(shape.bbox, layout.width, layout.height)
                    ),
                    provenance=Provenance(page=layout.index, engine="native"),
                    path=shape.path,
                    fill=shape.fill,
                    stroke=shape.stroke,
                    strokeWidth=shape.width,
                    dash=shape.dash or None,
                )
            )
        children.sort(key=lambda node: (node.bbox.y, node.bbox.x))
        for index, node in enumerate(children):
            node.z = index
        group = Node(
            id=new_ulid(),
            type=NodeType.group,
            role="section",
            bbox=BBox(x=0, y=0, w=layout.width, h=layout.height),
            editable=False,
            confidence=(
                round(sum(node.confidence for node in children) / len(children), 3)
                if children
                else 0.0
            ),
            provenance=Provenance(page=layout.index, engine="native"),
            children=children,
        )
        pages.append(
            Page(
                id=new_ulid(),
                size=Size(w=layout.width, h=layout.height),
                nodes=[group],
                referenceSha=reference_sha,
            )
        )

    review_items = _review_items(by_font, resolutions, probes, analysis, node_for_file)
    tokens = book.build(analysis)
    return Template(
        id=template_id,
        name=name,
        source=Source(
            fileName=file_name, sha256=sha256, pageCount=len(pages), kind="pdf"
        ),
        tokens=tokens,
        pages=pages,
        slots=build_slots(slot_sources),
        reviewItems=review_items,
    )


def _font_names(analysis: Analysis) -> list[str]:
    names: list[str] = []
    for layout in analysis.pages:
        for element in layout.elements:
            if element.font not in names:
                names.append(element.font)
    return names


def _review_items(
    by_font: dict[str, list[str]],
    resolutions: dict[str, FontResolution],
    probes: list[validators.TextProbe],
    analysis: Analysis,
    node_for_file: dict[str, str],
) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    counters: dict[str, int] = {}

    def add(
        kind: str,
        node_ids: list[str],
        severity: Severity,
        suggestion: str,
        confidence: float,
    ) -> None:
        counters[kind] = counters.get(kind, 0) + 1
        items.append(
            ReviewItem(
                id=f"{kind}-{counters[kind]:03d}",
                kind=kind,
                nodeIds=node_ids,
                severity=severity,
                suggestion=suggestion,
                confidence=confidence,
                autoFix=None,
            )
        )

    for requested, node_ids in by_font.items():
        resolution = resolutions[requested]
        if resolution.resolved is None:
            add(
                "font",
                node_ids,
                Severity.error,
                f"'{requested}' is not available locally. Choose a replacement font.",
                0.0,
            )
        elif resolution.certainty < 1.0:
            add(
                "font",
                node_ids,
                Severity.warn,
                f"Use {resolution.resolved} (metric-compatible substitute).",
                resolution.certainty,
            )
    for finding in validators.detect(probes, analysis.pages, node_for_file):
        add(
            finding.kind,
            finding.node_ids,
            finding.severity,
            finding.suggestion,
            finding.confidence,
        )
    return items


def confidence_of(template: Template) -> float:
    """Template confidence = area-weighted mean of leaf node confidences (architecture §6.6)."""
    total = 0.0
    area_sum = 0.0
    for page in template.pages:
        for group in page.nodes:
            for node in group.children or []:
                area = node.bbox.w * node.bbox.h
                if area <= 0:
                    continue
                total += node.confidence * area
                area_sum += area
    return round(total / area_sum, 3) if area_sum else 0.0
