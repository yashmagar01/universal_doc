"""Slots, shared slots and measured constraints (FR-ING-08/10)."""

from __future__ import annotations

from templix.ingest.slots import SlotSource, build_slots, violations
from templix.model import Constraints


def _source(node_id: str, page: int, role: str, text: str, max_lines: int = 1) -> SlotSource:
    return SlotSource(
        node_id=node_id, page=page, role=role, text=text, max_lines=max_lines, fit="shrink"
    )


def test_shared_footer_collapses_across_pages() -> None:
    sources = [
        _source("01AAAAAAAAAAAAAAAAAAAAAAAA", 0, "footer", "Campus Chronicle"),
        _source("01BBBBBBBBBBBBBBBBBBBBBBBB", 1, "footer", "Campus Chronicle"),
        _source("01CCCCCCCCCCCCCCCCCCCCCCCC", 2, "footer", "Different footer"),
    ]
    slots = build_slots(sources)
    assert len(slots) == 2
    shared = slots[0]
    assert shared.nodeIds == ["01AAAAAAAAAAAAAAAAAAAAAAAA", "01BBBBBBBBBBBBBBBBBBBBBBBB"]
    assert shared.constraints.maxChars == len("Campus Chronicle")
    assert [slot.label for slot in slots] == ["Footer 1", "Footer 2"]


def test_same_page_duplicates_stay_separate() -> None:
    sources = [
        _source("01AAAAAAAAAAAAAAAAAAAAAAAA", 0, "title", "Same"),
        _source("01BBBBBBBBBBBBBBBBBBBBBBBB", 0, "title", "Same"),
    ]
    slots = build_slots(sources)
    assert len(slots) == 2


def test_body_ordinals_and_constraints() -> None:
    text = "line one\nline two"
    slots = build_slots(
        [
            _source("01AAAAAAAAAAAAAAAAAAAAAAAA", 0, "body", text, max_lines=2),
            _source("01BBBBBBBBBBBBBBBBBBBBBBBB", 0, "body", "more"),
        ]
    )
    assert [slot.label for slot in slots] == ["Body text 1", "Body text 2"]
    assert slots[0].constraints.maxChars == len(text)
    assert slots[0].constraints.maxLines == 2
    assert slots[0].constraints.charsPerLine == 9


def test_original_passes_and_thirty_percent_fails() -> None:
    text = "University administration has officially ratified privacy initiative"
    constraints = Constraints(maxChars=len(text), maxLines=2, charsPerLine=len(text) // 2 + 1)
    assert violations(text, constraints) == []
    longer = text + "x" * (len(text) // 3 + 1)
    assert violations(longer, constraints)
