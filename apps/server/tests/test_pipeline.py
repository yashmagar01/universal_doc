"""Pipeline assembly on the fixture corpus: nodes, slots, review items, acceptance rules."""

from __future__ import annotations

import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import pymupdf
import pytest

from templix.ingest.native import PyMuPDFExtractor
from templix.ingest.native.export import export_document
from templix.ingest.pipeline import build_template, confidence_of
from templix.ingest.slots import violations
from templix.model import Document, Node, NodeType, Run, Slot, Template, new_ulid
from templix.store import BlobStore

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "generated"


def _build(tmp_path: Path, stem: str) -> tuple[Template, dict[str, Any]]:
    out = tmp_path / stem
    out.mkdir()
    extract = PyMuPDFExtractor().extract(str(FIXTURES / f"{stem}.pdf"), str(out), dpi=72)
    assert extract["ok"] is True
    template = build_template(
        extract,
        template_id="01HZZZZZZZZZZZZZZZZZZZZZZA",
        name=stem,
        file_name=f"{stem}.pdf",
        sha256="deadbeef",
        blob=BlobStore(tmp_path / "blobs"),
        out_dir=out,
    )
    return template, extract


def _leaves(template: Template) -> list[Node]:
    return [node for page in template.pages for group in page.nodes for node in group.children or []]


def _slot_for(template: Template, node_id: str) -> tuple[Node, Slot, str]:
    node = next(node for node in _leaves(template) if node.id == node_id)
    assert node.editable
    text = "".join(run.text for run in node.runs or [])
    slot = next(slot for slot in template.slots if node_id in slot.nodeIds)
    return node, slot, text


@pytest.fixture(scope="module")
def corpus(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Template]:
    root = tmp_path_factory.mktemp("pipeline")
    built: dict[str, Template] = {}
    for stem in ("newsletter_2col", "report_6page", "orientation_3page", "image_page"):
        built[stem] = _build(root, stem)[0]
    return built


def test_template_tokens_cover_node_styles(corpus: dict[str, Template]) -> None:
    template = corpus["newsletter_2col"]
    assert template.tokens.fonts
    assert template.tokens.textStyles
    for node in _leaves(template):
        if node.styleRef:
            assert node.styleRef in template.tokens.textStyles


def test_export_leaves_a_pre_prefill_document_untouched(
    tmp_path: Path, corpus: dict[str, Template]
) -> None:
    """Old drafts have empty content values; export must not redact them to blank."""
    template = corpus["newsletter_2col"]
    doc = Document(id=new_ulid(), templateId=template.id, templateVersion=1)
    out = tmp_path / "blank-doc.pdf"
    result = export_document(
        template, doc, str(FIXTURES / "newsletter_2col.pdf"), str(out)
    )
    assert result == {"ok": True, "editedSlots": 0, "warnings": []}
    pdf: Any = pymupdf.open(out)
    try:
        assert "CAMPUS CHRONICLE" in pdf[0].get_text()
    finally:
        pdf.close()


def test_export_preserves_vector_art_under_an_edited_label(
    tmp_path: Path, corpus: dict[str, Template]
) -> None:
    """Redacting a label inside a coloured panel must not delete the panel."""
    template = corpus["newsletter_2col"]
    slot = next(slot for slot in template.slots if slot.label == "Label 1")
    node = next(
        node
        for page in template.pages
        for group in page.nodes
        for node in group.children or []
        if node.id == slot.nodeIds[0]
    )
    doc = Document(id=new_ulid(), templateId=template.id, templateVersion=1)
    doc.content.values[slot.id] = [Run(text="Changed label")]
    out = tmp_path / "label.pdf"
    result = export_document(
        template, doc, str(FIXTURES / "newsletter_2col.pdf"), str(out)
    )
    assert result["warnings"] == []

    source: Any = pymupdf.open(FIXTURES / "newsletter_2col.pdf")
    exported: Any = pymupdf.open(out)
    try:
        page_no = node.provenance.page if node.provenance else 0
        assert len(exported[page_no or 0].get_drawings()) == len(
            source[page_no or 0].get_drawings()
        )
    finally:
        source.close()
        exported.close()


def test_newsletter_two_column_flow(corpus: dict[str, Template]) -> None:
    flows = [node for node in _leaves(corpus["newsletter_2col"]) if node.type == NodeType.flow]
    assert flows
    two_col = [node for node in flows if node.columns == 2]
    assert len(two_col) == 1
    node = two_col[0]
    assert node.columnGap == pytest.approx(17.4, abs=1.0)
    assert node.columnRule is False
    assert node.fit is not None and node.fit.mode == "reflow"
    assert node.fit.maxLines == 22


def test_nodes_ordered_and_grouped(corpus: dict[str, Template]) -> None:
    template = corpus["newsletter_2col"]
    for page in template.pages:
        assert len(page.nodes) == 1
        group = page.nodes[0]
        assert group.type == NodeType.group and group.role == "section"
        children = group.children or []
        assert [node.z for node in children] == list(range(len(children)))
        ys = [node.bbox.y for node in children]
        assert ys == sorted(ys)
        assert page.referenceSha is not None


def test_shared_footer_slot(corpus: dict[str, Template]) -> None:
    template = corpus["newsletter_2col"]
    footers = [slot for slot in template.slots if slot.label.startswith("Footer")]
    shared = [slot for slot in footers if len(slot.nodeIds) == 2]
    assert len(shared) == 1
    assert shared[0].constraints.maxChars == len(
        "Campus Chronicle - Student Affairs Publication Office"
    )


def test_pagenum_excluded_from_slots(corpus: dict[str, Template]) -> None:
    template = corpus["newsletter_2col"]
    pagenums = [node for node in _leaves(template) if node.role == "pagenum"]
    assert pagenums
    for node in pagenums:
        assert not node.editable
        assert all(node.id not in slot.nodeIds for slot in template.slots)


def test_font_pipeline_helvetica_alias(corpus: dict[str, Template]) -> None:
    template = corpus["newsletter_2col"]
    nodes = [node for node in _leaves(template) if node.fontResolution is not None]
    assert nodes
    for node in nodes:
        assert node.fontResolution is not None
        assert node.fontResolution.resolved == "Arial"
        assert node.fontResolution.certainty == 0.5
    fonts = [item for item in template.reviewItems if item.kind == "font"]
    assert fonts and all(item.severity.value == "warn" for item in fonts)
    assert all(item.id.startswith("font-") for item in fonts)


def test_review_item_ids_are_numbered(corpus: dict[str, Template]) -> None:
    template = corpus["image_page"]
    ids = [item.id for item in template.reviewItems]
    assert "imageDpi-001" in ids
    assert "font-001" in ids
    assert len(set(ids)) == len(ids)


def test_orientation_contrast_item(corpus: dict[str, Template]) -> None:
    template = corpus["orientation_3page"]
    contrast = [item for item in template.reviewItems if item.kind == "contrast"]
    assert len(contrast) == 1
    assert contrast[0].severity.value == "warn"
    assert contrast[0].confidence == 0.9


def test_image_page_dpi_item(corpus: dict[str, Template]) -> None:
    template = corpus["image_page"]
    dpi = [item for item in template.reviewItems if item.kind == "imageDpi"]
    assert len(dpi) == 1
    assert dpi[0].confidence == 0.95
    figures = sorted(
        (node for node in _leaves(template) if node.type == NodeType.image),
        key=lambda node: node.bbox.y,
    )
    assert len(figures) == 2
    assert dpi[0].nodeIds == [figures[0].id]  # the 8 dpi thumbnail, above the 150 dpi plate


def test_original_text_has_zero_violations(corpus: dict[str, Template]) -> None:
    for template in corpus.values():
        for page in template.pages:
            for group in page.nodes:
                for node in group.children or []:
                    if not node.editable or node.runs is None:
                        continue
                    _, slot, text = _slot_for(template, node.id)
                    assert violations(text, slot.constraints) == [], (template.name, node.role)


def test_thirty_percent_longer_violates(corpus: dict[str, Template]) -> None:
    template = corpus["newsletter_2col"]
    flow = next(node for node in _leaves(template) if node.type == NodeType.flow)
    _, slot, text = _slot_for(template, flow.id)
    longer = text + "x" * (len(text) // 3 + 1)
    assert violations(longer, slot.constraints)


def test_node_text_covers_pdf_text_layer(corpus: dict[str, Template]) -> None:
    """FR-ING-04 acceptance: >= 99 % of non-whitespace text-layer chars live in nodes."""
    def flat(text: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFC", text) if not ch.isspace())

    for stem, template in corpus.items():
        document: Any = pymupdf.open(str(FIXTURES / f"{stem}.pdf"))
        page_texts: list[str] = []
        for index in range(len(document)):
            page: Any = document.load_page(index)
            text: str = page.get_text()
            page_texts.append(text)
        document.close()
        source = "".join(page_texts)
        node_text = "".join(
            run.text
            for page in template.pages
            for group in page.nodes
            for node in group.children or []
            for run in (node.runs or [])
        )
        want = Counter(flat(source))
        have = Counter(flat(node_text))
        missing = sum((want - have).values())
        assert missing / max(sum(want.values()), 1) <= 0.01, stem


def test_confidence_in_range(corpus: dict[str, Template]) -> None:
    for template in corpus.values():
        value = confidence_of(template)
        assert 0.0 < value <= 1.0
