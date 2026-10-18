"""Patch application and inversion — the op-log core (§5.7, NFR-TEST-05).

A `Patch` is an ordered list of atomic `Op`s against a `Document`. Each op:

- ``apply(doc, op)``  → a new Document (pre-conditions enforced: locked layers are immutable),
- ``invert(doc, op)`` → the op that undoes it, computed against the *pre-apply* state.

The round-trip property (property-tested in ``tests/test_ops.py``):

    apply(invert_patch(doc, patch), apply(doc, patch)) == doc

Ops only touch content values and node overrides, so they never rewrite the template itself.
"""

from __future__ import annotations

from typing import Any, Literal

from .schema import Document, Run, StrictModel

MISSING: Any = object()

OpKind = Literal["set_slot", "clear_slot", "set_override", "remove_override"]


class Op(StrictModel):
    kind: OpKind
    slotId: str | None = None
    nodeId: str | None = None
    prop: str | None = None
    value: Any | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.kind in ("set_slot", "clear_slot") and self.slotId is None:
            raise ValueError("set_slot/clear_slot require slotId")
        if self.kind in ("set_override", "remove_override") and (
            self.nodeId is None or self.prop is None
        ):
            raise ValueError("override ops require nodeId and prop")


class Patch(StrictModel):
    ops: list[Op] = []  # noqa: RUF012 — pydantic deep-copies defaults per instance
    note: str | None = None


# --- helpers ---


def _get_slot(doc: Document, slot_id: str) -> list[Run] | None:
    return doc.content.values.get(slot_id)


def _override_present(doc: Document, node_id: str, prop: str) -> bool:
    return prop in doc.overrides.get(node_id, {})


def _override_get(doc: Document, node_id: str, prop: str) -> Any:
    return doc.overrides.get(node_id, {}).get(prop, MISSING)


def _check_unlocked(doc: Document, node_id: str, locked_nodes: frozenset[str] | None) -> None:
    if locked_nodes and node_id in locked_nodes:
        raise ValueError(f"node {node_id} is locked; locked layers are immutable")


# --- apply ---


def apply(doc: Document, op: Op, *, locked_nodes: frozenset[str] | None = None) -> Document:
    """Return a new Document with `op` applied. Raises ValueError on a violated pre-condition."""
    d = doc.model_copy(deep=True)
    k = op.kind

    if k == "set_slot":
        assert op.slotId is not None
        # `value` is typed Any (it varies by op kind); over HTTP slot runs arrive as plain dicts.
        raw: list[Any] = op.value or []
        runs = [v if isinstance(v, Run) else Run.model_validate(v) for v in raw]
        d.content.values[op.slotId] = runs
    elif k == "clear_slot":
        assert op.slotId is not None
        if op.slotId not in d.content.values:
            raise ValueError(f"slot {op.slotId} not set")
        del d.content.values[op.slotId]
    elif k == "set_override":
        assert op.nodeId is not None and op.prop is not None
        _check_unlocked(d, op.nodeId, locked_nodes)
        d.overrides.setdefault(op.nodeId, {})[op.prop] = op.value
    elif k == "remove_override":
        assert op.nodeId is not None and op.prop is not None
        if not _override_present(d, op.nodeId, op.prop):
            raise ValueError(f"override {op.nodeId}.{op.prop} not set")
        del d.overrides[op.nodeId][op.prop]
        if not d.overrides[op.nodeId]:
            del d.overrides[op.nodeId]
    else:  # pragma: no cover
        raise ValueError(f"unknown op kind {k}")
    return d


# --- invert ---


def invert(doc: Document, op: Op) -> Op:
    """The op that undoes `op`, computed against the pre-apply state `doc`."""
    k = op.kind
    if k == "set_slot":
        assert op.slotId is not None
        prior = _get_slot(doc, op.slotId)
        if prior is None:
            return Op(kind="clear_slot", slotId=op.slotId)
        return Op(kind="set_slot", slotId=op.slotId, value=prior)
    if k == "clear_slot":
        assert op.slotId is not None
        prior = _get_slot(doc, op.slotId)
        if prior is None:
            raise ValueError(f"slot {op.slotId} not set")
        return Op(kind="set_slot", slotId=op.slotId, value=prior)
    if k == "set_override":
        assert op.nodeId is not None and op.prop is not None
        prior = _override_get(doc, op.nodeId, op.prop)
        if prior is MISSING:
            return Op(kind="remove_override", nodeId=op.nodeId, prop=op.prop)
        return Op(kind="set_override", nodeId=op.nodeId, prop=op.prop, value=prior)
    if k == "remove_override":
        assert op.nodeId is not None and op.prop is not None
        prior = _override_get(doc, op.nodeId, op.prop)
        if prior is MISSING:
            raise ValueError(f"override {op.nodeId}.{op.prop} not set")
        return Op(kind="set_override", nodeId=op.nodeId, prop=op.prop, value=prior)
    raise ValueError(f"unknown op kind {k}")  # pragma: no cover


def apply_patch(doc: Document, patch: Patch, *, locked_nodes: frozenset[str] | None = None) -> Document:
    d = doc
    for op in patch.ops:
        d = apply(d, op, locked_nodes=locked_nodes)
    return d


def invert_patch(doc: Document, patch: Patch) -> Patch:
    """Inverse of `patch`, computed against pre-state `doc` (ops reversed, each inverted)."""
    inverse: list[Op] = []
    state = doc
    for op in patch.ops:
        inverse.append(invert(state, op))
        state = apply(state, op)
    return Patch(ops=list(reversed(inverse)), note=f"invert:{patch.note or ''}".strip(":"))
