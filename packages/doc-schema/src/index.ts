// AUTO-GENERATED from apps/server/templix/model (D-015) — do not edit by hand.
// Regenerate: uv run python -m templix.model.generate

export interface BBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Component {
  id: string;
  name: string;
  nodeIds?: string[];
  slotIds?: string[];
}

export interface Constraints {
  maxChars?: number | null;
  maxLines?: number | null;
  maxWords?: number | null;
  charsPerLine?: number | null;
  fit?: string | null;
  aspect?: string | null;
  minDpi?: number | null;
}

export interface Content {
  values?: Record<string, Run[]>;
  instances?: Record<string, Record<string, unknown>[]>;
  assets?: Record<string, Record<string, unknown>>;
}

export interface Document {
  schemaVersion?: number;
  id: string;
  templateId: string;
  templateVersion: number;
  content?: Content;
  overrides?: Record<string, Record<string, unknown>>;
  status?: DocumentStatus;
}

export type DocumentStatus = "draft" | "review" | "final";

export interface Fidelity {
  pages?: FidelityPage[];
  overall?: number | null;
}

export interface FidelityPage {
  ssim?: number | null;
  pixelDiff?: number | null;
  textIoU?: number | null;
}

export interface Fit {
  mode?: "shrink" | "clip" | "grow" | "reflow";
  minScale?: number;
  maxLines?: number | null;
}

export type FitMode = "cover" | "contain";

export interface FontDef {
  family: string;
  weights?: number[];
  source?: FontSource;
}

export interface FontResolution {
  requested: string;
  resolved?: string | null;
  source?: FontSource | null;
  certainty?: number;
}

export type FontSource = "system" | "google" | "local";

export interface Node {
  id: string;
  type: NodeType;
  role: string;
  name?: string | null;
  bbox: BBox;
  z?: number;
  rotation?: number;
  locked?: boolean;
  editable?: boolean;
  visible?: boolean;
  confidence?: number;
  provenance?: Provenance | null;
  groupId?: string | null;
  styleRef?: string | null;
  runs?: Run[] | null;
  fit?: Fit | null;
  align?: "left" | "center" | "right" | "justify" | null;
  columns?: number | null;
  columnGap?: number | null;
  columnRule?: boolean | null;
  fontResolution?: FontResolution | null;
  assetId?: string | null;
  crop?: BBox | null;
  fitMode?: FitMode | null;
  aspectLock?: boolean | null;
  minDpi?: number | null;
  path?: string | null;
  fill?: string | null;
  stroke?: string | null;
  strokeWidth?: number | null;
  dash?: number[] | null;
  radius?: number | null;
  rows?: number | null;
  cols?: number | null;
  children?: Node[] | null;
}

export type NodeType = "text" | "image" | "shape" | "table" | "group" | "flow";

export interface Op {
  kind: "set_slot" | "clear_slot" | "set_override" | "remove_override";
  slotId?: string | null;
  nodeId?: string | null;
  prop?: string | null;
  value?: unknown | null;
}

export interface Page {
  id: string;
  size: Size;
  nodes?: Node[];
  referenceSha?: string | null;
}

export interface Patch {
  ops?: Op[];
  note?: string | null;
}

export interface Provenance {
  page?: number | null;
  pdfObjects?: number[];
  engine?: string | null;
}

export interface Repeater {
  id: string;
  componentId: string;
  containerNodeId: string;
  direction?: "stack" | "grid";
  gap?: number;
  min?: number;
  max?: number;
  overflow?: "flag" | "clip" | "new-page";
}

export interface ReviewItem {
  id: string;
  kind: string;
  nodeIds?: string[];
  severity?: Severity;
  suggestion?: string | null;
  confidence?: number;
  autoFix?: Record<string, unknown> | null;
}

export interface Rule {
  id: string;
  scope: Scope;
  kind: RuleKind;
  params?: Record<string, unknown>;
  severity?: Severity;
  message?: string | null;
}

export type RuleKind = "maxChars" | "maxLines" | "minFontSize" | "allowedFonts" | "minContrast" | "safeMargin" | "requiredOnEveryPage" | "imageMinDpi" | "aspectLock" | "noOverflow";

export interface Run {
  text: string;
  marks?: string[];
}

export type Scope = "global" | "page" | "role" | "node";

export interface Section {
  id: string;
  label: string;
  slotIds?: string[];
}

export type Severity = "error" | "warn" | "info";

export interface Size {
  w: number;
  h: number;
}

export interface Slot {
  id: string;
  nodeIds: string[];
  field?: string | null;
  label: string;
  kind: SlotKind;
  constraints?: Constraints;
  required?: boolean;
  section?: string | null;
}

export type SlotKind = "text" | "richtext" | "image" | "date" | "link" | "choice";

export interface Source {
  fileName?: string | null;
  sha256?: string | null;
  pageCount?: number;
  kind?: "pdf" | "blank" | "template";
}

export interface Spacing {
  margins?: Record<string, number>;
  gutter?: number;
  baseline?: number;
}

export interface Template {
  schemaVersion?: number;
  id: string;
  name: string;
  version?: number;
  source?: Source;
  tokens?: Tokens;
  pages?: Page[];
  sections?: Section[];
  slots?: Slot[];
  components?: Component[];
  repeaters?: Repeater[];
  rules?: Rule[];
  reviewItems?: ReviewItem[];
  fidelity?: Fidelity | null;
}

export interface TextStyle {
  font: string;
  size: number;
  leading: number;
  tracking?: number;
  color?: string | null;
  transform?: "uppercase" | "lowercase" | "none" | null;
}

export interface Tokens {
  colors?: Record<string, string>;
  fonts?: Record<string, FontDef>;
  textStyles?: Record<string, TextStyle>;
  spacing?: Spacing;
}
