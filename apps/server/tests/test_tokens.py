"""Style tokens on the fixture corpus (FR-ING-09)."""

from __future__ import annotations

from pathlib import Path

import pytest

from templix.ingest.heuristics import analyse
from templix.ingest.native import PyMuPDFExtractor
from templix.ingest.tokens import Palette, StyleBook, build_palette
from templix.model import FontSource

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "generated"


@pytest.fixture(scope="module")
def newsletter(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    out = tmp_path_factory.mktemp("tokens")
    extract = PyMuPDFExtractor().extract(
        str(FIXTURES / "newsletter_2col.pdf"), str(out), dpi=72
    )
    assert extract["ok"] is True
    return extract


def test_palette_naming_and_cap(newsletter: dict[str, object]) -> None:
    palette = build_palette(newsletter)
    assert len(palette.colors) <= 12
    assert palette.colors["paper"] == "#FFFFFF"
    assert palette.name("#FFFFFF") == "paper"
    assert palette.name("#FEFEFE") == "paper"  # within deltaE 3 of the cluster
    accent = palette.colors["accent"]
    assert accent.upper() in ("#0A66C2", "#1A994D")
    assert palette.name("#000000") == "ink"


def test_spacing_and_gutter(newsletter: dict[str, object]) -> None:
    analysis = analyse(newsletter)
    book = StyleBook(build_palette(newsletter))
    tokens = book.build(analysis)
    assert tokens.spacing.margins["left"] == 48.0
    assert tokens.spacing.gutter == 17.4
    assert tokens.spacing.baseline == 13.0


def test_style_book_collisions_and_reuse() -> None:
    book = StyleBook(Palette([("#111111", 10), ("#FFFFFF", 5)]))
    first = book.style_ref(
        "body", size=10.0, leading=13.0, color_hex="#111111", bold=False,
        family="Arial", source=FontSource.system,
    )
    assert first == "body"
    again = book.style_ref(
        "body", size=10.0, leading=13.0, color_hex="#111111", bold=False,
        family="Arial", source=FontSource.system,
    )
    assert again == "body"  # identical signature reuses the style
    second = book.style_ref(
        "body", size=12.0, leading=15.0, color_hex="#111111", bold=False,
        family="Arial", source=FontSource.system,
    )
    assert second == "body2"
    book.style_ref(
        "title", size=30.0, leading=36.0, color_hex="#111111", bold=True,
        family="Arial", source=FontSource.system,
    )
    assert book.fonts["text"].family == "Arial"
    assert book.fonts["display"].weights == [700]
    assert book.text_styles["body"].color == "ink"
