"""Generate `packages/doc-schema` (JSON Schema + TypeScript) from the Pydantic models (D-015).

    uv run python -m templix.model.generate

Output is deterministic (stable ordering, no timestamps), so `scripts/check.ps1` can regenerate and
`git diff` the committed files — the schema-freshness gate.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from . import patch as patch_module
from . import schema as schema_module

_SERVER_ROOT = Path(__file__).resolve().parents[2]
_DOC_SCHEMA = _SERVER_ROOT.parents[1] / "packages" / "doc-schema"

HEADER = (
    "// AUTO-GENERATED from apps/server/templix/model (D-015) — do not edit by hand.\n"
    "// Regenerate: uv run python -m templix.model.generate\n"
)


def _model_classes() -> list[type[BaseModel]]:
    found: list[type[BaseModel]] = []
    for mod in (schema_module, patch_module):
        for obj in vars(mod).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and obj is not BaseModel
                and obj.__module__ == mod.__name__
                and obj.model_fields  # skip the field-less StrictModel base
            ):
                found.append(obj)
    return sorted(found, key=lambda c: c.__name__)


def _collect_defs(models: list[type[BaseModel]]) -> dict[str, dict[str, Any]]:
    defs: dict[str, dict[str, Any]] = {}
    for model in models:
        schema = model.model_json_schema()
        nested: dict[str, dict[str, Any]] = schema.get("$defs") or {}
        for name, spec in nested.items():
            defs.setdefault(name, spec)
        root = {k: v for k, v in schema.items() if k != "$defs"}
        defs.setdefault(model.__name__, root)
    return dict(sorted(defs.items()))


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _array(elem: str) -> str:
    return f"({elem})[]" if ("|" in elem or "&" in elem) else f"{elem}[]"


def _inline_object(spec: dict[str, Any]) -> str:
    required: set[str] = set(spec.get("required") or [])
    props: dict[str, dict[str, Any]] = spec.get("properties") or {}
    body = "; ".join(f"{p}{'' if p in required else '?'}: {_ts(ps)}" for p, ps in props.items())
    return f"{{ {body} }}"


def _ts(spec: dict[str, Any]) -> str:
    """Render a JSON Schema fragment as a TypeScript type."""
    if "allOf" in spec:
        parts: list[dict[str, Any]] = spec["allOf"] or []
        return " & ".join(_ts(p) for p in parts)
    if "anyOf" in spec:
        variants: list[dict[str, Any]] = spec["anyOf"] or []
        return " | ".join(_ts(v) for v in variants)
    if "$ref" in spec:
        return _ref_name(spec["$ref"])
    if "const" in spec:
        return json.dumps(spec["const"])
    if "enum" in spec:
        values: list[Any] = spec["enum"] or []
        return " | ".join(json.dumps(v) for v in values)

    t = spec.get("type")
    if t == "string":
        return "string"
    if t in ("number", "integer"):
        return "number"
    if t == "boolean":
        return "boolean"
    if t == "null":
        return "null"
    if t == "array":
        items: dict[str, Any] = spec.get("items") or {}
        return _array(_ts(items))

    # object with inline properties -> literal type
    if "properties" in spec:
        return _inline_object(spec)
    # mapping (dict[str, T])
    if t == "object" or "additionalProperties" in spec:
        extra: dict[str, Any] | bool | None = spec.get("additionalProperties")
        if isinstance(extra, dict):
            return f"Record<string, {_ts(extra)}>"
        if extra is False:
            return "Record<string, never>"
        return "Record<string, unknown>"
    # no type constraint at all (pydantic `Any` -> `{}`)
    return "unknown"


def _emit_def(name: str, spec: dict[str, Any]) -> str:
    if "enum" in spec:
        values: list[Any] = spec["enum"] or []
        return f"export type {name} = {' | '.join(json.dumps(v) for v in values)};"
    if "properties" in spec:
        required: set[str] = set(spec.get("required") or [])
        props: dict[str, dict[str, Any]] = spec.get("properties") or {}
        lines = [f"export interface {name} {{"]
        for prop, pspec in props.items():
            opt = "" if prop in required else "?"
            lines.append(f"  {prop}{opt}: {_ts(pspec)};")
        lines.append("}")
        return "\n".join(lines)
    return f"export type {name} = {_ts(spec)};"


def render() -> tuple[str, str]:
    """Return `(typescript, json)` for the current models — pure, no I/O (so it is testable)."""
    defs = _collect_defs(_model_classes())

    ts = HEADER + "\n" + "\n\n".join(_emit_def(n, s) for n, s in defs.items()) + "\n"
    schema_doc = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$defs": defs}
    schema_json = json.dumps(schema_doc, indent=2, ensure_ascii=False) + "\n"
    return ts, schema_json


def render_openapi() -> str:
    """The FastAPI OpenAPI document as committed JSON — part of the freshness gate."""
    from ..api.app import create_app

    with tempfile.TemporaryDirectory() as tmp:
        app = create_app(Path(tmp) / "home")
        try:
            doc: dict[str, Any] = app.openapi()
        finally:
            app.state.engine.dispose()  # release the SQLite file so the temp dir can be removed
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def generate() -> tuple[Path, Path, Path]:
    ts, schema_json = render()
    openapi_json = render_openapi()
    ts_path = _DOC_SCHEMA / "src" / "index.ts"
    json_path = _DOC_SCHEMA / "schema" / "schema.json"
    openapi_path = _DOC_SCHEMA / "schema" / "openapi.json"
    for path in (ts_path, json_path, openapi_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    _write(ts_path, ts)
    _write(json_path, schema_json)
    _write(openapi_path, openapi_json)
    return ts_path, json_path, openapi_path


def _write(path: Path, text: str) -> None:
    # newline="\n" keeps LF on every OS so the committed output is byte-identical everywhere.
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


if __name__ == "__main__":
    ts_out, json_out, openapi_out = generate()
    print(f"wrote {ts_out}\nwrote {json_out}\nwrote {openapi_out}")
