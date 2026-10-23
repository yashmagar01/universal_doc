"""Validator scans (FR-ING-13): contrast / clipped / overlap / image dpi."""

from __future__ import annotations

from templix.ingest.heuristics import Figure, PageLayout, Shape
from templix.ingest.validators import TextProbe, contrast_ratio, detect


def _shape(x0: float, y0: float, x1: float, y1: float, fill: str | None) -> Shape:
    return Shape(
        page=0, role="box", path="", fill=fill, stroke=None, width=0.0,
        dash=[], x0=x0, y0=y0, x1=x1, y1=y1,
    )


def _figure(dpi: float, file: str = "img-0.png") -> Figure:
    return Figure(
        page=0, file=file, x0=0, y0=0, x1=100, y1=100,
        px_w=100, px_h=100, dpi=dpi, mask=False,
    )


def _probe(color: str, size: float = 10.0, bold: bool = False) -> TextProbe:
    return TextProbe(
        node_id="01AAAAAAAAAAAAAAAAAAAAAAAA", page=0,
        x0=10, y0=10, x1=110, y1=30, color=color, size=size, bold=bold,
    )


def test_contrast_pair() -> None:
    assert contrast_ratio("#FFFFFF", "#0A66C2") >= 4.5  # newsletter caption passes
    assert contrast_ratio("#FFFFFF", "#1A994D") < 4.5  # orientation caption fails
    assert contrast_ratio("#000000", "#FFFFFF") > 20


def test_contrast_over_box_and_outside() -> None:
    layout = PageLayout(index=0, width=612, height=792, shapes=[_shape(0, 0, 200, 200, "#1A994D")])
    inside = _probe("#FFFFFF", size=12.0, bold=True)  # white on green, small bold
    outside = TextProbe(
        node_id="01BBBBBBBBBBBBBBBBBBBBBBBB", page=0,
        x0=300, y0=300, x1=400, y1=320, color="#000000", size=12.0, bold=False,
    )
    findings = detect([inside, outside], [layout], {})
    assert [f.kind for f in findings] == ["contrast"]
    assert findings[0].node_ids == [inside.node_id]


def test_clipped_and_overlap_and_dpi() -> None:
    clipped = TextProbe(
        node_id="01AAAAAAAAAAAAAAAAAAAAAAAA", page=0,
        x0=-5, y0=400, x1=100, y1=420, color="#000000", size=10.0, bold=False,
    )
    a = TextProbe(
        node_id="01BBBBBBBBBBBBBBBBBBBBBBBB", page=0,
        x0=10, y0=10, x1=110, y1=30, color="#000000", size=10.0, bold=False,
    )
    b = TextProbe(
        node_id="01CCCCCCCCCCCCCCCCCCCCCCCC", page=0,
        x0=15, y0=12, x1=115, y1=32, color="#000000", size=10.0, bold=False,
    )
    layout = PageLayout(index=0, width=612, height=792, figures=[_figure(dpi=8.0)])
    findings = detect([clipped, a, b], [layout], {"img-0.png": "01DDDDDDDDDDDDDDDDDDDDDDDD"})
    kinds = [f.kind for f in findings]
    assert kinds == ["clipped", "overlap", "imageDpi"]
    assert findings[1].node_ids == [a.node_id, b.node_id]
    assert findings[2].node_ids == ["01DDDDDDDDDDDDDDDDDDDDDDDD"]
