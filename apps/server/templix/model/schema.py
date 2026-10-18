"""Pydantic domain models — the source of truth (D-015).

Everything persisted or exposed over the API derives from these: OpenAPI, JSON Schema and the
generated TypeScript in `packages/doc-schema` all come out of this module. Units are PDF points,
top-left origin, y down (§5.2). `schemaVersion` is stamped on every persisted object (§5.7).
"""

from __future__ import annotations

import re
import secrets
import time
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = 1

# --- ULID: 48-bit timestamp + 80-bit random, Crockford base32, 26 chars (§5.3 "id (ULID)") ---
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def new_ulid() -> str:
    ts = int(time.time() * 1000)
    rand = secrets.randbits(80)
    value = (ts << 80) | rand
    chars = [_CROCKFORD[0]] * 26
    for i in range(25, -1, -1):
        chars[i] = _CROCKFORD[value & 0x1F]
        value >>= 5
    return "".join(chars)


ULID = Annotated[str, Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")]


def _check_ulid(v: str) -> str:
    if not _ULID_RE.match(v):
        raise ValueError(f"not a ULID: {v!r}")
    return v


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


# --- Enumerations (controlled vocabularies, §5.3 / §5.4 / §5.5) ---


class NodeType(StrEnum):
    text = "text"
    image = "image"
    shape = "shape"
    table = "table"
    group = "group"
    flow = "flow"


class SlotKind(StrEnum):
    text = "text"
    richtext = "richtext"
    image = "image"
    date = "date"
    link = "link"
    choice = "choice"


class RuleKind(StrEnum):
    maxChars = "maxChars"
    maxLines = "maxLines"
    minFontSize = "minFontSize"
    allowedFonts = "allowedFonts"
    minContrast = "minContrast"
    safeMargin = "safeMargin"
    requiredOnEveryPage = "requiredOnEveryPage"
    imageMinDpi = "imageMinDpi"
    aspectLock = "aspectLock"
    noOverflow = "noOverflow"


class Scope(StrEnum):
    global_ = "global"
    page = "page"
    role = "role"
    node = "node"


class Severity(StrEnum):
    error = "error"
    warn = "warn"
    info = "info"


class FitMode(StrEnum):
    cover = "cover"
    contain = "contain"


class DocumentStatus(StrEnum):
    draft = "draft"
    review = "review"
    final = "final"


# --- Primitives (§5.2) ---


class BBox(StrictModel):
    x: float
    y: float
    w: float
    h: float


class Size(StrictModel):
    w: float
    h: float


class Run(StrictModel):
    text: str
    marks: list[str] = []


class Fit(StrictModel):
    mode: Literal["shrink", "clip", "grow", "reflow"] = "shrink"
    minScale: float = 1.0
    maxLines: int | None = None


class Provenance(StrictModel):
    page: int | None = None
    pdfObjects: list[int] = []
    engine: str | None = None


class FontResolution(StrictModel):
    """D-018 cascade result for one node's font. `resolved=None` means nothing matched (review item)."""

    requested: str
    resolved: str | None = None
    source: FontSource | None = None
    certainty: float = Field(default=1.0, ge=0.0, le=1.0)


# --- Nodes (§5.3) ---


class Node(StrictModel):
    """A layout node. Payload fields are optional and gated by `type` (text -> runs, image ->
    assetId, group -> children, …). A single model keeps one JSON schema / one TS type; the
    per-type payloads are enforced by `validate_payload` below rather than a discriminated union."""

    id: ULID
    type: NodeType
    role: str
    name: str | None = None
    bbox: BBox
    z: int = 0
    rotation: float = 0.0
    locked: bool = False
    editable: bool = True
    visible: bool = True
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: Provenance | None = None
    groupId: str | None = None

    # text / flow
    styleRef: str | None = None
    runs: list[Run] | None = None
    fit: Fit | None = None
    align: Literal["left", "center", "right", "justify"] | None = None
    columns: int | None = None
    columnGap: float | None = None
    columnRule: bool | None = None
    fontResolution: FontResolution | None = None
    # image
    assetId: str | None = None
    crop: BBox | None = None
    fitMode: FitMode | None = None
    aspectLock: bool | None = None
    minDpi: int | None = None
    # shape
    path: str | None = None
    fill: str | None = None
    stroke: str | None = None
    strokeWidth: float | None = None
    dash: list[float] | None = None
    radius: float | None = None
    # table / group
    rows: int | None = None
    cols: int | None = None
    children: list[Node] | None = None

    @field_validator("id")
    @classmethod
    def _ulid(cls, v: str) -> str:
        return _check_ulid(v)

    @field_validator("fill", "stroke")
    @classmethod
    def _hex(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$", v):
            raise ValueError(f"colour must be #RRGGBB[AA]: {v!r}")
        return v.upper() if len(v) == 7 else v


# --- Slots, sections, rules, components, repeaters (§5.4 / §5.5) ---


class Constraints(StrictModel):
    maxChars: int | None = None
    maxLines: int | None = None
    maxWords: int | None = None
    fit: str | None = None
    aspect: str | None = None
    minDpi: int | None = None


class Slot(StrictModel):
    id: ULID
    nodeIds: list[ULID]
    field: str | None = None
    label: str
    kind: SlotKind
    constraints: Constraints = Constraints()
    required: bool = False
    section: str | None = None

    @field_validator("id", "nodeIds")
    @classmethod
    def _ulids(cls, v: Any) -> Any:
        if isinstance(v, str):
            return _check_ulid(v)
        return [_check_ulid(x) for x in v]


class Section(StrictModel):
    id: str
    label: str
    slotIds: list[ULID] = []


class Rule(StrictModel):
    id: str
    scope: Scope
    kind: RuleKind
    params: dict[str, Any] = {}
    severity: Severity = Severity.error
    message: str | None = None


class Component(StrictModel):
    id: str
    name: str
    nodeIds: list[ULID] = []
    slotIds: list[ULID] = []


class Repeater(StrictModel):
    id: str
    componentId: str
    containerNodeId: ULID
    direction: Literal["stack", "grid"] = "stack"
    gap: float = 0.0
    min: int = 1
    max: int = 20
    overflow: Literal["flag", "clip", "new-page"] = "flag"


# --- Tokens (§5.5) ---


class FontSource(StrEnum):
    system = "system"
    google = "google"
    local = "local"


class FontDef(StrictModel):
    family: str
    weights: list[int] = []
    source: FontSource = FontSource.system


class TextStyle(StrictModel):
    font: str
    size: float
    leading: float
    tracking: float = 0.0
    color: str | None = None
    transform: Literal["uppercase", "lowercase", "none"] | None = None


class Spacing(StrictModel):
    margins: dict[str, float] = {}
    gutter: float = 0.0
    baseline: float = 0.0


class Tokens(StrictModel):
    colors: dict[str, str] = {}
    fonts: dict[str, FontDef] = {}
    textStyles: dict[str, TextStyle] = {}
    spacing: Spacing = Spacing()


# --- Pages / source / fidelity ---


class Page(StrictModel):
    id: str
    size: Size
    nodes: list[Node] = []


class Source(StrictModel):
    fileName: str | None = None
    sha256: str | None = None
    pageCount: int = 0
    kind: Literal["pdf", "blank", "template"] = "blank"


class FidelityPage(StrictModel):
    ssim: float | None = None
    pixelDiff: float | None = None
    textIoU: float | None = None


class Fidelity(StrictModel):
    pages: list[FidelityPage] = []
    overall: float | None = None


# --- Template / Content / Document (§5.1) ---


class Template(StrictModel):
    schemaVersion: int = SCHEMA_VERSION
    id: ULID
    name: str
    version: int = 1
    source: Source = Source()
    tokens: Tokens = Field(default_factory=Tokens)
    pages: list[Page] = []
    sections: list[Section] = []
    slots: list[Slot] = []
    components: list[Component] = []
    repeaters: list[Repeater] = []
    rules: list[Rule] = []
    fidelity: Fidelity | None = None

    @field_validator("id")
    @classmethod
    def _ulid(cls, v: str) -> str:
        return _check_ulid(v)


class Content(StrictModel):
    values: dict[str, list[Run]] = {}
    instances: dict[str, list[dict[str, Any]]] = {}
    assets: dict[str, dict[str, Any]] = {}


class Document(StrictModel):
    schemaVersion: int = SCHEMA_VERSION
    id: ULID
    templateId: ULID
    templateVersion: int
    content: Content = Field(default_factory=Content)
    overrides: dict[str, dict[str, Any]] = {}
    status: DocumentStatus = DocumentStatus.draft

    @field_validator("id", "templateId")
    @classmethod
    def _ulid(cls, v: str) -> str:
        return _check_ulid(v)
