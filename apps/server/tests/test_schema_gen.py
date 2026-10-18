"""Generated doc-schema tests (D-015): deterministic, faithful TS + JSON Schema + OpenAPI output."""

from __future__ import annotations

import json
from typing import Any

from templix.model.generate import render, render_openapi


def test_render_is_deterministic() -> None:
    assert render() == render()


def test_typescript_covers_domain_models() -> None:
    ts, _ = render()
    for name in ("Template", "Document", "Patch", "Op", "Node", "Slot", "Rule"):
        assert f"export interface {name} " in ts
    assert "export type NodeType =" in ts  # StrEnum -> string-literal union
    assert "value?: unknown" in ts  # `Any` -> unknown, never a fabricated object type


def test_json_schema_is_structured_and_refs_resolve() -> None:
    _, schema_json = render()
    doc: Any = json.loads(schema_json)
    defs: Any = doc["$defs"]
    assert {"Template", "Document", "Op", "Run"} <= set(defs)
    assert defs["Template"]["properties"]["pages"]["items"]["$ref"] == "#/$defs/Page"
    assert "Page" in defs
    # `Op.value` is `Any | None`: the open `{}` schema stays open (not narrowed to an object).
    assert defs["Op"]["properties"]["value"]["anyOf"] == [{}, {"type": "null"}]


def test_render_openapi_describes_the_api() -> None:
    first, second = render_openapi(), render_openapi()
    assert first == second  # deterministic -> the freshness gate never flaps
    doc: Any = json.loads(first)
    assert doc["openapi"].startswith("3.")
    assert doc["info"]["title"] == "Templix"
    for path in ("/status", "/templates", "/documents/{doc_id}/ops", "/jobs", "/providers/{name}/key"):
        assert path in doc["paths"]
