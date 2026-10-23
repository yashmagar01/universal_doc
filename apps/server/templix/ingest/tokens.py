"""Style tokens from the extracted layer (FR-ING-09, architecture §5.5).

Palette: sRGB -> CIELAB (D65), greedy merge at deltaE76 < 3, capped at 12; the special
names go to the darkest cluster (`ink`), the lightest cluster with L > 80 (`paper`), and
the highest chroma (`accent`); the rest are `color3`, `color4`, ... by weight.

Text styles are keyed by role with a numeric suffix on collisions: the first style built
for a role takes the bare role name, later distinct signatures get `body2`, `body3`...

# ponytail: text style signatures ignore tracking/transform (extraction cannot see letter
# spacing reliably); add then when a fixture needs them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..model import FontDef, FontSource, Spacing, TextStyle, Tokens
from .heuristics import Analysis

LAB_FLOOR = 80.0  # paper candidate lightness
DELTA_E = 3.0  # merge distance
PALETTE_CAP = 12


def _lab(hex_color: str) -> tuple[float, float, float]:
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255

    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linear(r), linear(g), linear(b)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def _delta(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.dist(a, b)


@dataclass
class _Cluster:
    hex: str
    lab: tuple[float, float, float]
    weight: int
    name: str = ""


class Palette:
    def __init__(self, entries: list[tuple[str, int]]) -> None:
        clusters: list[_Cluster] = []
        for hex_color, weight in sorted(entries, key=lambda e: -e[1]):
            lab = _lab(hex_color)
            for cluster in clusters:
                if _delta(cluster.lab, lab) < DELTA_E:
                    cluster.weight += weight
                    break
            else:
                clusters.append(_Cluster(hex_color, lab, weight))
        if not clusters:
            clusters = [_Cluster("#000000", _lab("#000000"), 1)]
        clusters.sort(key=lambda c: -c.weight)
        clusters = clusters[:PALETTE_CAP]
        self._assign_names(clusters)
        self._clusters = clusters
        self.colors: dict[str, str] = {c.name: c.hex for c in clusters}

    @staticmethod
    def _assign_names(clusters: list[_Cluster]) -> None:
        remaining = list(clusters)
        darkest = min(remaining, key=lambda c: c.lab[0])
        darkest.name = "ink"
        remaining.remove(darkest)
        papers = [c for c in remaining if c.lab[0] > LAB_FLOOR]
        if papers:
            paper = max(papers, key=lambda c: c.lab[0])
            paper.name = "paper"
            remaining.remove(paper)
        if remaining:
            accent = max(remaining, key=lambda c: math.hypot(c.lab[1], c.lab[2]))
            accent.name = "accent"
            remaining.remove(accent)
        for index, cluster in enumerate(remaining, start=3):
            cluster.name = f"color{index}"

    def name(self, hex_color: str) -> str:
        lab = _lab(hex_color)
        return min(self._clusters, key=lambda c: _delta(c.lab, lab)).name


def build_palette(extract: dict[str, Any]) -> Palette:
    entries: dict[str, int] = {}
    for page in extract["pages"]:
        for span in page["spans"]:
            hex_color = str(span["color"])
            entries[hex_color] = entries.get(hex_color, 0) + max(len(str(span["text"])), 1)
        for vector in page["vectors"]:
            for key in ("fill", "stroke"):
                hex_color = vector.get(key)
                if hex_color:
                    entries[str(hex_color)] = entries.get(str(hex_color), 0) + 1
    return Palette(list(entries.items()))


class StyleBook:
    """Assigns styleRefs and accumulates the token tables while nodes are built."""

    def __init__(self, palette: Palette) -> None:
        self.palette = palette
        self.fonts: dict[str, FontDef] = {}
        self.text_styles: dict[str, TextStyle] = {}
        self._signatures: dict[tuple[str, str, float, float, str], str] = {}
        self._counts: dict[str, int] = {}

    def style_ref(
        self,
        role: str,
        *,
        size: float,
        leading: float,
        color_hex: str,
        bold: bool,
        family: str,
        source: FontSource,
    ) -> str:
        font_token = "display" if bold else "text"
        if font_token not in self.fonts:
            self.fonts[font_token] = FontDef(
                family=family,
                weights=[700] if bold else [400],
                source=source,
            )
        color = self.palette.name(color_hex)
        signature = (role, font_token, round(size, 1), round(leading, 1), color)
        if signature in self._signatures:
            return self._signatures[signature]
        count = self._counts.get(role, 0) + 1
        self._counts[role] = count
        name = role if count == 1 else f"{role}{count}"
        self.text_styles[name] = TextStyle(
            font=font_token, size=size, leading=leading, color=color
        )
        self._signatures[signature] = name
        return name

    def build(self, analysis: Analysis) -> Tokens:
        return Tokens(
            colors=dict(self.palette.colors),
            fonts=dict(self.fonts),
            textStyles=dict(self.text_styles),
            spacing=_spacing(analysis),
        )


def _spacing(analysis: Analysis) -> Spacing:
    lefts: list[float] = []
    tops: list[float] = []
    rights: list[float] = []
    bottoms: list[float] = []
    gutter = 0.0
    for page in analysis.pages:
        if not page.elements:
            continue
        lefts.append(min(el.bbox[0] for el in page.elements))
        tops.append(min(el.bbox[1] for el in page.elements))
        rights.append(page.width - max(el.bbox[2] for el in page.elements))
        bottoms.append(page.height - max(el.bbox[3] for el in page.elements))
        for element in page.elements:
            if element.column_gap:
                gutter = max(gutter, element.column_gap)
    return Spacing(
        margins={
            "top": round(min(tops), 1) if tops else 0.0,
            "right": round(min(rights), 1) if rights else 0.0,
            "bottom": round(min(bottoms), 1) if bottoms else 0.0,
            "left": round(min(lefts), 1) if lefts else 0.0,
        },
        gutter=round(gutter, 1),
        baseline=analysis.baseline,
    )
