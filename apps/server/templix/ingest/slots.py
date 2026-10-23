"""Slots and measured constraints (FR-ING-08/10, architecture §5.4).

One slot per editable text/flow/image node. Roles whose text repeats verbatim across
pages - running header, footer, masthead title - collapse into ONE shared slot bound to
every occurrence (FR-ING-08). Constraints come from the original: maxChars = original
length, maxLines = measured line count, charsPerLine = ceil(maxChars / maxLines), so
replacing the text with the original passes and a 30 % longer string violates.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from ..model import Constraints, Slot, SlotKind, new_ulid

LABELS: dict[str, str] = {
    "title": "Title",
    "header": "Running header",
    "footer": "Footer",
    "heading1": "Heading 1",
    "heading2": "Heading 2",
    "body": "Body text",
    "caption": "Caption",
    "label": "Label",
    "quote": "Quote",
    "byline": "Byline",
}

SHARED_ROLES = {"header", "footer", "title"}
DEFAULT_MIN_DPI = 150


@dataclass
class SlotSource:
    node_id: str
    page: int
    role: str
    text: str
    max_lines: int
    fit: str
    kind: str = "text"
    min_dpi: int | None = None


def violations(text: str, constraints: Constraints) -> list[str]:
    """Constraint checks used by FR-ING-10's acceptance test and the rules gate."""
    failed: list[str] = []
    if constraints.maxChars is not None and len(text) > constraints.maxChars:
        failed.append("maxChars")
    if (
        constraints.maxLines is not None
        and constraints.charsPerLine is not None
        and len(text) > constraints.maxLines * constraints.charsPerLine
    ):
        failed.append("maxLines")
    if constraints.maxWords is not None and len(text.split()) > constraints.maxWords:
        failed.append("maxWords")
    return failed


def _make_slot(group: list[SlotSource]) -> Slot:
    primary = group[0]
    node_ids = [source.node_id for source in group]
    if primary.kind == "image":
        return Slot(
            id=new_ulid(),
            nodeIds=node_ids,
            label=LABELS.get(primary.role, "Image"),
            kind=SlotKind.image,
            constraints=Constraints(minDpi=primary.min_dpi or DEFAULT_MIN_DPI),
        )
    max_chars = min(len(source.text) for source in group)
    max_lines = min(source.max_lines for source in group)
    chars_per_line = ceil(max_chars / max_lines) if max_lines else None
    return Slot(
        id=new_ulid(),
        nodeIds=node_ids,
        label=LABELS.get(primary.role, primary.role.title()),
        kind=SlotKind.text,
        constraints=Constraints(
            maxChars=max_chars,
            maxLines=max_lines,
            charsPerLine=chars_per_line,
            fit=primary.fit,
        ),
    )


def build_slots(sources: list[SlotSource]) -> list[Slot]:
    """Build slots in emission order; shared groups are keyed (role, exact text)."""
    slots: list[Slot] = []
    claimed: set[int] = set()
    for index, source in enumerate(sources):
        if index in claimed:
            continue
        group = [index]
        if source.role in SHARED_ROLES and source.text:
            for other_index, other in enumerate(sources):
                if (
                    other_index != index
                    and other_index not in claimed
                    and other.role == source.role
                    and other.text == source.text
                ):
                    group.append(other_index)
            if len({sources[i].page for i in group}) < 2:
                group = [index]  # same-page duplicates stay separate
        claimed.update(group)
        slots.append(_make_slot([sources[i] for i in group]))
    counts: dict[str, int] = {}
    for slot in slots:
        counts[slot.label] = counts.get(slot.label, 0) + 1
    ordinals: dict[str, int] = {}
    for slot in slots:
        if counts[slot.label] > 1:
            ordinals[slot.label] = ordinals.get(slot.label, 0) + 1
            slot.label = f"{slot.label} {ordinals[slot.label]}"
    return slots
