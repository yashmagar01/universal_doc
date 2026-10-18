# Templix — Decision Log

Status: living document. Every architectural decision that is hard to reverse lives here.
**Rule for the coding agent:** if you must deviate from a decision, do not silently deviate. Add a new
entry (`D-0xx`, status `Proposed`), explain why, and flag it in your milestone report. Never edit an
`Accepted` entry's decision text; supersede it instead.

Legend: **Accepted** = build on it · **Provisional** = build on it, but the owner (Yash) may flip it ·
**Open** = needs an answer from Yash (see §Open questions) · **Deferred** = intentionally postponed.

Cross-references: `FR-*` = `functional-requirements.md`, `NFR-*` = `non-functional-requirements.md`,
architecture sections are `§` in `system-architecture.md`.

---

## Index

| ID | Title | Status |
|----|-------|--------|
| D-001 | Product shape: local web app = React SPA + local Python server | Accepted |
| D-002 | A document is data, not code (AI never emits code files) | Accepted |
| D-003 | Three-tier model: Template / Content / Document | Accepted |
| D-004 | Hybrid layout model: frames + flow regions + repeaters | Accepted |
| D-005 | Reference study = fusion of native PDF layer and vision/semantic layer | Accepted |
| D-006 | Parsing engines are pluggable adapters; v1 ships native + optional VLM-via-user-key | Accepted |
| D-007 | PyMuPDF for extraction; project licensed AGPL-3.0 | Provisional |
| D-008 | One render-core for preview and export (headless Chromium) | Accepted |
| D-009 | Own thin provider adapters over official SDKs, not LiteLLM | Accepted |
| D-010 | API keys are held by the local server in the OS keyring, never by the browser | Accepted |
| D-011 | AI output contract: validated patch operations, deterministic interview, fit loop | Accepted |
| D-012 | Privacy messaging is state-driven and honest; consent + data-flow ledger | Accepted |
| D-013 | Frontend stack: Vite + React 19 + TypeScript + Tailwind v4 | Accepted |
| D-014 | Backend stack: Python 3.12+, FastAPI, Pydantic v2, SQLite | Accepted |
| D-015 | Pydantic is the schema source of truth; TS types and validators are generated | Accepted |
| D-016 | One change mechanism: patches (undo/redo, autosave, AI proposals) | Accepted |
| D-017 | Rules engine: declarative JSON rules, single TypeScript implementation | Accepted |
| D-018 | Fonts are self-hosted; a font resolver cascade handles missing fonts | Accepted |
| D-019 | Design fidelity to Stitch, with a documented list of corrections | Accepted |
| D-020 | v1 scope exclusions | Accepted |
| D-021 | DOCX input is normalised to PDF through LibreOffice (Phase 2) | Deferred |
| D-022 | Scanned PDFs through an OCR adapter (Phase 2) | Deferred |
| D-023 | Fidelity is measured, never asserted (round-trip score) | Accepted |
| D-024 | Distribution: scripts in v1, Tauri sidecar later | Deferred |
| D-025 | Monorepo with pnpm workspaces + uv | Accepted |
| D-026 | No telemetry | Accepted |
| D-027 | Model identifiers are never hard-coded | Accepted |
| D-028 | Rich text is stored as typed spans, never as HTML | Accepted |
| D-029 | Local models (Ollama etc.) arrive later through the OpenAI-compatible adapter | Deferred |
| D-030 | Hosted OCR services (including ocr.z.ai) are not used | Accepted |

---

## D-001 — Product shape: local web app = React SPA + local Python server
**Status:** Accepted
**Context.** Reference study needs heavy PDF libraries (PyMuPDF, Pillow, scikit-image, optional layout
models) that are Python-native. Provider API keys must be kept somewhere safer than page JavaScript. Some
provider endpoints are awkward to call directly from a browser (CORS, extra opt-in headers). Departments
care about where documents go.
**Decision.** Templix runs on the user's machine as two processes: a React SPA served by Vite (dev) or by
the Python server (prod) and a FastAPI server bound to `127.0.0.1`. The SPA talks only to that server.
The server talks to LLM providers on the user's behalf.
**Alternatives rejected.**
- *Pure in-browser app (pdf.js + WASM):* weaker extraction, keys live in page JS, CORS friction.
- *Hosted SaaS:* contradicts the privacy story and adds ops/cost.
- *Electron/Tauri from day one:* packaging cost before the product is proven (see D-024).
**Consequences.** Two runtimes to install (Node for building, Python to run); solved later by packaging.
Local-server hardening becomes a first-class concern (§10 of architecture; NFR-SEC-*).

## D-002 — A document is data, not code
**Status:** Accepted
**Context.** The original pain: AI agents "recreate" a report by writing `.py`/`.js` that draws it, and
any small change regenerates the whole file, burning tokens and breaking fidelity.
**Decision.** The canonical representation is a structured model (Template + Content JSON, §5). The AI
never emits code or whole documents. It emits **patch operations** against Content (D-011), a few dozen
tokens each. A deterministic renderer (D-008) turns the model into pixels/PDF.
**Consequences.** Cost per edit is small and bounded; fidelity cannot be damaged by a model because it
cannot touch locked layers; every AI action is reviewable and undoable.

## D-003 — Three-tier model: Template / Content / Document
**Status:** Accepted
**Decision.**
- **Template** = layers (nodes), style tokens, slots, components, rules, provenance. Changes rarely.
- **Content** = values bound to slots plus repeater instances. Changes every issue.
- **Document** = reference to a Template version + a Content + per-document overrides.
**Consequences.** "Change one headline" touches exactly one Content value. Template edits are explicit,
versioned, and separate from authoring. Template packages (`.templix`) are shareable between committees.

## D-004 — Hybrid layout model
**Status:** Accepted
**Context.** Pure absolute positioning reproduces the reference perfectly but cannot absorb longer text,
extra articles, or multi-column flow. Pure flow layout (CSS/Word style) cannot reproduce a designed page.
**Decision.** Nodes are **frames** (absolute boxes in PDF points) by default. Two extensions exist:
**flow regions** (a frame whose text flows across CSS columns) and **repeaters** (a component that can be
instantiated N times and stacked inside a region, see §5.4). Text fit is handled per slot (`fit` policy).
**Consequences.** Pixel-faithful by default; flexibility exactly where newsletters need it.
Cross-page flow (text continuing onto a new page) is **out of v1** (FR-TPL-14).

## D-005 — Reference study = fusion of two sources
**Status:** Accepted
**Context.** Benchmarked OCR/document models (PaddleOCR-VL, GLM-OCR, MinerU, dots.ocr) are tuned for
text, tables and formulas as Markdown/JSON. They do not preserve exact geometry, vectors, or fonts.
The PDF's own drawing layer has exact geometry but no semantics.
**Decision.** Run a **native pass** (positions, fonts, colours, images, vector paths from the PDF) and a
**semantic pass** (roles, reading order, grouping), then **fuse** them: native geometry is authoritative
for how it looks, the semantic pass is authoritative for what it is. Each node carries a confidence.
**Consequences.** Design survives. Low-confidence items go to a human review queue (FR-ING-*, FR-TPL-*).

## D-006 — Parsing engines are pluggable adapters
**Status:** Accepted
**Decision.** Define a `LayoutEngine` port. v1 adapters: (a) `native` (always on, deterministic
heuristics), (b) `vlm` (page images + extracted text to the user's chosen vision model, **opt-in per
document with consent**, D-012). Later adapters (Phase 2+): `docling`, `pp-doclayout`, `paddleocr-vl`,
`glm-ocr` (self-hosted weights, MIT), `rapidocr`. Choose by measured round-trip score on the real corpus
(D-023), not by leaderboard.
**Consequences.** We are not locked to any model; benchmark claims (mostly self-reported) are not trusted
without our own test.

## D-007 — PyMuPDF for extraction; project licensed AGPL-3.0
**Status:** Provisional (needs Yash's confirmation — OQ-1)
**Context.** PyMuPDF gives the richest access (spans with font/size/colour, images, vector drawings) but
is AGPL/commercial dual-licensed.
**Decision.** Use PyMuPDF and release Templix under **AGPL-3.0**. If Yash later wants a permissive or
closed-source licence, swap the extractor behind the `NativeExtractor` port to `pypdfium2` (+ `pdfminer.six`
for text metadata) or buy the commercial licence.
**Consequences.** All code touching PyMuPDF stays behind one module (`apps/server/templix/ingest/native/`).

## D-008 — One render-core for preview and export
**Status:** Accepted
**Decision.** A TypeScript package `render-core` converts a resolved document (Template + Content) into a
DOM subtree. The browser preview uses it directly. PDF export loads the same render route in headless
Chromium (Playwright) and calls `page.pdf()` with print CSS and exact page size. Text fitting and
measurement also live in `render-core`.
**Alternatives rejected.** WeasyPrint/Typst/ReportLab (a second renderer means preview ≠ output);
`html2canvas`+`jsPDF` (rasterises text); wkhtmltopdf (unmaintained).
**Consequences.** WYSIWYG by construction. Requires Chromium (installed through Playwright).

## D-009 — Own thin provider adapters, not LiteLLM
**Status:** Accepted
**Decision.** `LLMProvider` protocol with adapters over the **official SDKs**: `openai`, `anthropic`,
`google-genai`, plus an **OpenAI-compatible** adapter taking `base_url`, `api_key`, `model` (covers
OpenRouter, Groq, Together, LM Studio, vLLM and — later — Ollama, D-029). Adapters expose:
`list_models`, `complete`, `stream`, `test`, capabilities.
**Alternatives rejected.** LiteLLM: broad surface and a large transitive dependency tree for what is three
providers and one compatible protocol; harder to audit for a tool that handles API keys. Revisit if the
provider list grows past ~6.
**Consequences.** We own request/response normalisation (~300 lines per adapter) but control retries,
redaction, and structured-output strategy.

## D-010 — Keys live in the OS keyring, held by the server
**Status:** Accepted (supersedes the Stitch copy "encrypted in browser IndexedDB")
**Context.** Encrypting in IndexedDB with a key stored beside it in the same browser profile gives little
protection, and exposes the key to any script in the page.
**Decision.** Keys are submitted once (`PUT /providers/{id}/key`, write-only) and stored with the
`keyring` library (Windows Credential Manager / macOS Keychain / Secret Service). Fallback when no keyring
exists: an encrypted file protected by a user passphrase (scrypt + AES-GCM). The SPA only ever sees
`{provider, label, last4, status}`. Logs redact anything matching key patterns.
**Consequences.** "Show key" eye icon in the mock applies **only while typing a new key**; stored keys
cannot be revealed (the user re-enters to rotate).

## D-011 — AI output contract
**Status:** Accepted
**Decision.**
1. AI Assist is an **interview** whose *plan* is deterministic (derived from template sections and slots).
   The LLM drafts content and may word questions, but does not decide what to ask.
2. The model's only write channel is a **list of patch operations** constrained by a JSON Schema and
   limited to editable slots (§9). Anything else is rejected before the user sees it.
3. Proposals are shown as a diff (before/after) for **Accept / Reject**; nothing applies silently.
4. After a proposal, a **fit loop** measures the result in `render-core`; on overflow the violations are
   sent back for up to 2 repair attempts, then surfaced to the user.
5. Context is a compact **slot digest**, not the document (§9.4). Stable prefix first to benefit from
   provider prompt caching.
**Consequences.** Predictable cost, no whole-file regeneration, model-agnostic, safe against prompt
injection from document text (§10.4).

## D-012 — Privacy messaging is state-driven and honest
**Status:** Accepted (supersedes Stitch copy "100% On-Device", "Zero cloud upload", "FERPA/Student
Privacy" claims)
**Context.** With bring-your-own-key, selected document text (and optionally page images) **does** leave
the machine when the user chooses a cloud model. Blanket "100% on-device" copy would be false, and a
compliance claim (FERPA) is a legal statement the product cannot make.
**Decision.**
- The app is "local": storage, parsing, rendering, export, and key custody are on the user's machine.
- A persistent **data-flow indicator** shows the truth for the current action: *No data leaves this
  device* (manual mode, native parsing) or *Sends slot text to \<Provider\>* / *Sends page images to
  \<Provider\>*.
- First use of each provider per document requires a **consent dialog** listing what is sent.
- A local **data-flow ledger** records every outbound call (provider, model, doc, categories, tokens,
  time). Visible in Settings → Privacy. Exportable.
- No legal-compliance claims anywhere in the UI or docs.
**Consequences.** Trust comes from accurate, inspectable behaviour. Local models (D-029) later flip the
indicator to "stays on device" for AI too.

## D-013 — Frontend stack
**Status:** Accepted
**Decision.** Vite + React 19 + TypeScript (strict) + Tailwind CSS v4 (CSS-first `@theme` tokens from
`design.md`), React Router, Zustand + Immer (state + patches), TanStack Query (server state), Radix UI
primitives (accessibility), Tiptap (constrained rich text), `react-resizable-panels` (split viewer),
`pdfjs-dist` (original-PDF viewer), `react-easy-crop` (image crop), `diff` (text diff).
**Alternatives rejected.** Next.js (no SSR need; local app), Redux (heavier), Konva/Fabric canvas editors
(text fidelity, accessibility and DOM measuring are better with real DOM), CSS-in-JS.
**Consequences.** Matches Yash's existing React 19 + Tailwind v4 experience.

## D-014 — Backend stack
**Status:** Accepted
**Decision.** Python ≥ 3.12, FastAPI + Uvicorn, Pydantic v2, SQLAlchemy 2 + Alembic on SQLite (WAL),
in-process `asyncio` jobs with a `ProcessPoolExecutor` for CPU/parsing work, SSE for progress and token
streaming. Package/venv management with `uv`.
**Alternatives rejected.** Celery/Redis (needless infrastructure for a single-user local app), Django.
**Consequences.** Zero services to run besides the app itself.

## D-015 — Pydantic is the schema source of truth
**Status:** Accepted
**Decision.** Domain models are Pydantic v2 classes in `apps/server/templix/model/`. FastAPI emits OpenAPI;
`openapi-typescript` generates TS types into `packages/doc-schema`; the JSON Schema for Template/Content/
Patch is exported to `packages/doc-schema/schema/*.json` and used by Ajv in the SPA. A CI check fails if
generated files are stale. `schemaVersion` + migration functions guard persisted data.
**Consequences.** One definition, no drift between Python and TS.

## D-016 — One change mechanism: patches
**Status:** Accepted
**Decision.** All Content/Template mutations are expressed as RFC 6902-style operations applied through the
store (Immer produces them). The same operations power undo/redo, the persisted op-log (autosave and
section history), and AI proposals. The server validates every incoming op against the schema, node
ownership (`locked`, `editable`), and rules before persisting.

## D-017 — Rules engine
**Status:** Accepted
**Decision.** Rules are declarative JSON (`maxChars`, `maxLines`, `minFontSize`, `allowedFonts`,
`minContrast`, `safeMargin`, `requiredOnEveryPage`, `imageMinDpi`, `aspectLock`, `custom`-expression is
**not** allowed in v1). One TypeScript implementation (`packages/rules`) runs in the browser (live
feedback) and inside the headless export page (gate before export). No second implementation in Python.

## D-018 — Fonts
**Status:** Accepted
**Decision.** No runtime Google Fonts CDN. Inter and Material Symbols are bundled. A **font resolver**
maps PDF font names (subset prefix stripped, e.g. `ABCDEF+Inter-SemiBold`) to: (1) user-supplied font files
→ (2) bundled/installed families → (3) an on-demand download from the Google Fonts API cached locally (only
with user consent, Settings → Fonts) → (4) a metric-compatible fallback with a visible warning.
Embedded PDF fonts are subsets and are **not** reused for new text.

## D-019 — Fidelity to Stitch, with corrections
**Status:** Accepted
**Decision.** The six Stitch screens are the visual contract. Differences are limited to the table in
`design.md §12 "Stitch defects and required corrections"`. Canonical canvas colour is `#F3F2EF`
(Stitch's own DESIGN.md says so, but its screens use `#F4F3F0`/`#FAF9F6` inconsistently).

## D-020 — v1 scope exclusions
**Status:** Accepted
Not in v1: accounts/login, cloud sync, real-time collaboration, dark theme, mobile-first layouts (desktop
first, graceful down to 1024 px), DOCX **export**, voice input (the mic icon in the AI composer is hidden),
cross-page text flow, CMYK/PDF-X print production, plugin marketplace.

## D-021 — DOCX input via LibreOffice
**Status:** Deferred (Phase 2)
**Decision.** DOCX is converted to PDF with headless LibreOffice (optional system dependency), then follows
the normal pipeline. If LibreOffice is absent, DOCX upload is disabled with an explanatory message.
**Why not native DOCX parsing now.** Different geometry semantics (flow, not absolute); doubles the
ingestion surface. Revisit after PDF quality is proven.

## D-022 — Scanned PDFs
**Status:** Deferred (Phase 2)
**Decision.** Detect pages without a usable text layer; route through an OCR adapter (RapidOCR/Tesseract
locally, or the `vlm` adapter with consent). Flag the template "Reconstructed from image — review needed".

## D-023 — Fidelity is measured, never asserted
**Status:** Accepted
**Decision.** After ingestion Templix re-renders the template with its original content and compares it to
the reference per page (SSIM + masked pixel diff + text-box IoU, §6.5). The UI shows that number and a diff
heatmap. Numbers like "99.4 % pixel-matched" or "92 % confident" in the mockups are placeholders and
**must be computed**, never hard-coded. Round-trip tests on a fixture corpus gate CI (NFR-FID-*).

## D-024 — Distribution
**Status:** Deferred
**Decision.** v1: `pnpm install && uv sync && pnpm dev` and a `make run` production-like script.
Later: Tauri shell launching the Python server as a sidecar (PyInstaller/uv-bundled), single installer.

## D-025 — Monorepo
**Status:** Accepted
**Decision.** pnpm workspaces (`apps/web`, `packages/*`) plus a `uv` project in `apps/server`. Single git
repo, conventional commits, one `make check` that runs lint, types, unit, and schema-freshness checks.

## D-026 — No telemetry
**Status:** Accepted
No analytics, no crash upload, no update pings in v1. Local rotating logs only, with redaction. The footer
text "No telemetry" in the mockup becomes true by construction (NFR-PRIV-*).

## D-027 — Model identifiers are never hard-coded
**Status:** Accepted
**Context.** The mockups show model names that are already outdated (e.g. `gpt-4o`,
`claude-3-5-sonnet-20241022`, `gemini-1.5-pro`).
**Decision.** Model lists come from each provider's *list models* endpoint at runtime, merged with a
user-editable `model-capabilities.json` (vision, structured-output mode, context window, optional price per
million tokens). Unknown models are allowed with conservative capability defaults. A "recommended" flag is
data, not code.

## D-028 — Rich text as typed spans
**Status:** Accepted
**Decision.** Slot text is `Span[]` = `{text, marks: ("bold"|"italic"|{"link": url})[]}` grouped in
paragraphs. Never stored or rendered as HTML. Links are limited to `http(s):` and `mailto:`. This removes
an XSS class and makes model output trivially validatable.

## D-029 — Local models later
**Status:** Deferred
**Decision.** Ollama/LM Studio are added through the OpenAI-compatible adapter with presets
(`http://localhost:11434/v1`). The Settings screen already contains the card, shown **disabled with a
"Coming soon" tag** in v1. When enabled, the data-flow indicator reports "stays on this device".
Local OCR/layout models (PaddleOCR-VL, GLM-OCR) arrive as `LayoutEngine` adapters (D-006).

## D-030 — No hosted OCR
**Status:** Accepted
**Context.** `ocr.z.ai` is a demo front end for GLM-OCR; the hosted API would send documents to a third
party. The *model weights* are MIT-licensed and can be self-hosted.
**Decision.** Do not integrate any hosted OCR/parsing API. Self-host open weights only, and only in later
phases (D-006, D-029).

---

## Open questions for Yash

| ID | Question | Why it matters | Default if unanswered |
|----|----------|----------------|-----------------------|
| OQ-1 | Licence: is open source under AGPL-3.0 OK, or do you want permissive/closed? | Drives D-007 (PyMuPDF vs pypdfium2) | AGPL-3.0 |
| OQ-2 | Please provide 5–10 real reference PDFs (newsletter/magazine/report) for the fixture corpus. May they be committed to a **private** repo? | Without real fixtures the fidelity work is guesswork | Agent builds synthetic fixtures; real ones kept untracked |
| OQ-3 | Which OS do you and the committee use (Windows/macOS/Linux)? | Keyring, fonts, packaging | Support all three; test Windows first |
| OQ-4 | Do your documents contain Marathi/Hindi (Devanagari) text? | Complex-script shaping, font choice (Noto Sans Devanagari) | Treated as Should (FR-ING-18, NFR-I18N-02) |
| OQ-5 | Is the final deliverable always PDF, or do you also need editable DOCX? | DOCX export is Won't in v1 | PDF only |
| OQ-6 | Which cloud providers will you actually use first? | Order of adapter polish | OpenAI-compatible, Anthropic, Google |
| OQ-7 | Do the reference PDFs ever come from Canva/Word/InDesign where you still have the source? | If sources exist, a native import could beat PDF reverse-engineering | Ignore sources in v1 |
