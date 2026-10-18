"""Property tests for op apply/invert round-trip (NFR-TEST-05).

For any document and any forward patch of valid ops:

    apply_patch(invert_patch(doc, patch), apply_patch(doc, patch)) == doc
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from templix.model import Document, Op, Patch, Run, apply_patch, invert_patch, new_ulid

SLOTS = [f"sl_{i}" for i in range(3)]
NODES = [new_ulid() for _ in range(3)]
PROPS = ["x", "y", "text", "size"]


def base_doc() -> Document:
    d = Document(id=new_ulid(), templateId=new_ulid(), templateVersion=1)
    # seed one slot and one override so the "prior present" path is exercised
    d.content.values["sl_0"] = [Run(text="seed")]
    d.overrides[NODES[0]] = {"x": 10}
    return d


def _set_slot(slot: str, text: str) -> Op:
    return Op(kind="set_slot", slotId=slot, value=[Run(text=text)])


def _set_override(node: str, prop: str, value: object) -> Op:
    return Op(kind="set_override", nodeId=node, prop=prop, value=value)


override_value: st.SearchStrategy[object] = st.one_of(
    st.integers(-100, 100), st.text(max_size=5), st.booleans()
)
slot_strategy: st.SearchStrategy[Op] = st.builds(
    _set_slot, st.sampled_from(SLOTS), st.text(alphabet="abc", min_size=1, max_size=5)
)
override_strategy: st.SearchStrategy[Op] = st.builds(
    _set_override, st.sampled_from(NODES), st.sampled_from(PROPS), override_value
)
op_strat: st.SearchStrategy[Op] = st.one_of(slot_strategy, override_strategy)


@settings(max_examples=100, deadline=None)
@given(st.lists(op_strat, min_size=1, max_size=8))
def test_apply_invert_roundtrip(ops: list[Op]) -> None:
    doc = base_doc()
    patch = Patch(ops=ops)
    forward = apply_patch(doc, patch)
    backward = apply_patch(forward, invert_patch(doc, patch))
    assert backward == doc


def test_invert_of_seed_restore() -> None:
    doc = base_doc()
    patch = Patch(ops=[Op(kind="set_slot", slotId="sl_0", value=[Run(text="changed")])])
    forward = apply_patch(doc, patch)
    assert forward.content.values["sl_0"] != doc.content.values["sl_0"]
    assert apply_patch(forward, invert_patch(doc, patch)) == doc


def test_locked_node_rejects_override() -> None:
    doc = base_doc()
    locked = frozenset({NODES[0]})
    with pytest.raises(ValueError, match="locked"):
        apply_patch(
            doc,
            Patch(ops=[Op(kind="set_override", nodeId=NODES[0], prop="x", value=1)]),
            locked_nodes=locked,
        )
