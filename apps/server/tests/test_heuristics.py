"""Heuristic roles/elements/columns on the fixture corpus (FR-ING-05/06/07).

Expected values are the calibrated geometry of `fixtures/generate.py`, probed with PyMuPDF
before writing the thresholds - see the calibration notes in `templix/ingest/heuristics.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from templix.ingest.heuristics import Analysis, Element, analyse
from templix.ingest.native import PyMuPDFExtractor

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "generated"
NAMES = [
    "newsletter_2col.pdf",
    "report_6page.pdf",
    "exec_weekly_1page.pdf",
    "orientation_3page.pdf",
    "image_page.pdf",
]


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analysis]:
    out = tmp_path_factory.mktemp("heuristics")
    results: dict[str, Analysis] = {}
    for name in NAMES:
        extract = PyMuPDFExtractor().extract(str(FIXTURES / name), str(out / name), dpi=72)
        assert extract["ok"] is True, extract
        results[name] = analyse(extract)
    return results


def _elements(analysis: Analysis, role: str, page: int | None = None) -> list[Element]:
    pages = analysis.pages if page is None else [analysis.pages[page]]
    return [el for layout in pages for el in layout.elements if el.role == role]


def test_body_size_is_10_on_every_fixture(analyses: dict[str, Analysis]) -> None:
    for name, analysis in analyses.items():
        assert analysis.body_size == 10.0, name


def test_newsletter_columns_and_gap(analyses: dict[str, Analysis]) -> None:
    analysis = analyses["newsletter_2col.pdf"]
    flow = [el for el in analysis.pages[0].elements if el.columns == 2]
    assert len(flow) == 1
    assert flow[0].role == "body"
    assert flow[0].column_gap is not None and abs(flow[0].column_gap - 17.4) <= 1.0
    assert len(flow[0].lines) == 22
    # reading order is column-major: left column first
    assert all(line.x0 == 48.0 for line in flow[0].lines[:12])
    assert all(line.x0 == 310.0 for line in flow[0].lines[12:])
    page_one_body = [el for el in analysis.pages[1].elements if el.role == "body"]
    assert [el.columns for el in page_one_body] == [1]  # full-width flow on page 2


def test_newsletter_roles_and_shared_furniture(analyses: dict[str, Analysis]) -> None:
    analysis = analyses["newsletter_2col.pdf"]
    assert analysis.baseline == 13.0
    titles = _elements(analysis, "title")
    assert [el.text for el in titles] == ["CAMPUS CHRONICLE"] * 2
    assert len(_elements(analysis, "header")) == 2  # kicker, both pages
    assert len(_elements(analysis, "footer")) == 2
    assert {el.text for el in _elements(analysis, "pagenum")} == {"Page 1 of 2", "Page 2 of 2"}
    labels = {el.text for el in _elements(analysis, "label")}
    assert labels == {"[Story Photo - Students at the laboratory]", "Callout quote:"}
    heading = _elements(analysis, "heading1")
    assert [el.text for el in heading] == [
        "New Local AI Laboratories Open for Collaborative\nResearch Projects",
        "This Week on Campus",
    ]


def test_report_single_column_and_furniture(analyses: dict[str, Analysis]) -> None:
    analysis = analyses["report_6page.pdf"]
    assert analysis.baseline == 22.0
    assert all(el.columns == 1 for layout in analysis.pages for el in layout.elements)
    assert len(_elements(analysis, "title")) >= 1
    assert len(_elements(analysis, "footer")) == 6
    assert {el.text for el in _elements(analysis, "pagenum")} == {
        f"Page {n} of 6" for n in range(1, 7)
    }


def test_exec_weekly_roles(analyses: dict[str, Analysis]) -> None:
    analysis = analyses["exec_weekly_1page.pdf"]
    assert len(_elements(analysis, "header")) == 1
    assert len(_elements(analysis, "title")) == 1
    assert {el.text for el in _elements(analysis, "heading2")} == {"Decisions", "Action Items"}
    assert {el.text for el in _elements(analysis, "footer")} == {"Executive Committee Weekly"}
    assert {el.text for el in _elements(analysis, "pagenum")} == {"Page 1 of 1"}


def test_orientation_bracket_label(analyses: dict[str, Analysis]) -> None:
    analysis = analyses["orientation_3page.pdf"]
    labels = [el.text for el in _elements(analysis, "label")]
    assert any(text.startswith("[Campus Map") for text in labels)
    assert all(
        el.text.startswith("[") for el in _elements(analysis, "label") if el.size == 12.0
    )


def test_image_page_captions_and_top_zone_body(analyses: dict[str, Analysis]) -> None:
    analysis = analyses["image_page.pdf"]
    bodies = _elements(analysis, "body")
    assert bodies and bodies[0].text.startswith("Figures below show")
    assert {el.text for el in _elements(analysis, "caption")} == {
        "Figure 1 - reference plate (150 dpi)",
        "Figure 2 - thumbnail (8 dpi)",
    }
    figures = analysis.pages[0].figures
    assert [fig.role for fig in figures] == ["figure", "figure"]
    assert sorted(round(fig.dpi) for fig in figures) == [8, 150]
