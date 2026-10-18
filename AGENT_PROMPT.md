# MASTER PROMPT — Build "Templix" (hand this to your coding agent)

> Paste this whole file as the first message to the coding agent (Claude Code, Antigravity, Cursor, etc.),
> with the repository containing `docs/` and `design/stitch/` from this bundle. Keep it as `AGENTS.md`
> / `CLAUDE.md` at the repo root so every session starts with it.

---

## 0. Your role

You are the lead engineer building **Templix**, a local-first web application that turns old reference
documents (PDF newsletters, magazines, reports) into **layered, rule-aware templates** and lets the user
recreate new documents by changing only the content. Behave like a staff-level engineer: design before you
code, keep changes small and tested, challenge ambiguity, and never fake results.

The product owner is **Yash** (student developer, Government Polytechnic Awasari, head of his department
committee's magazine/newsletter team). Primary users are student-committee and office teams who must follow
strict formats. Quality of the output (fidelity, correctness) matters more than feature count.

## 1. Read these first (in this order) — they are the specification

1. `docs/decisions.md` — 30 accepted decisions (D-001…D-030) and open questions (OQ-1…OQ-7).
2. `docs/system-architecture.md` — containers, domain model, pipelines, AI subsystem, security, API.
3. `docs/functional-requirements.md` — IDs `FR-*` with acceptance criteria.
4. `docs/non-functional-requirements.md` — IDs `NFR-*` with measurable targets and gates.
5. `docs/design.md` — tokens, components, per-screen specs, copy deck, **Stitch defects to correct (§12)**.
6. `docs/dependencies.md` — approved libraries, versions policy, licences, rejected options.
7. `design/stitch/` — the visual contract: six screens, each `screen.png` (look at it!) and `code.html`
   (reference markup only), plus `professional_document_canvas/DESIGN.md`. If you cannot view images, rely on
   `design.md §8` and read the `code.html` files for structure.

If two documents disagree, precedence is: **decisions.md > system-architecture.md > design.md >
functional/non-functional requirements > Stitch files**. Report any contradiction you find.

## 2. Product in ten lines

1. User uploads a reference PDF → **ingestion job** extracts every text span, image, vector shape with exact
   geometry (PyMuPDF) and assigns roles/groups (heuristics now, optional VLM later) → **Template** with
   layers, style tokens, slots, constraints, rules, confidence and a **fidelity score** (D-005, D-023).
2. The user reviews/corrects the analysis (layer tree, inspector, canvas overlays) and saves the Template.
3. A **Document** = Template + Content. Content changes never touch the template (D-003).
4. **Manual Edit:** auto-generated sidebar form + live preview. **AI Assist:** deterministic interview + model
   drafts content → **validated patch operations** → user Accept/Reject (D-011).
5. One **render-core** (TypeScript) draws the preview and, via headless Chromium, the exported PDF (D-008).
6. Providers: bring-your-own API key (OpenAI, Anthropic, Google, any OpenAI-compatible endpoint). Keys live in
   the OS keyring on the local server, never in the browser (D-009, D-010). Local models (Ollama) come later.
7. Everything runs on the user's machine: React SPA + FastAPI on `127.0.0.1` + SQLite (D-001).
8. Privacy is **honest and visible**: indicators, consent dialog, data-flow ledger (D-012). No telemetry.
9. Light theme only; Stitch design is the visual target, with the corrections in `design.md §12`.
10. Every number the UI shows (confidence, fidelity, counters, RAM, cost) is **computed**.

## 3. Non-negotiable invariants (violating any of these is a bug)

- **Document = data, never code.** The AI never writes code or whole files; it returns patch ops (§9.6 of
  architecture). Do not add any "generate script" path.
- **AI can write only `/content/**` for editable slots.** Locked layers are immutable (NFR-FID-03). Server and
  client both enforce this; tests prove it (NFR-SEC-07).
- **API keys:** write-only endpoint; stored in OS keyring (fallback encrypted file); never logged, never
  returned, never in the DB/browser/URL (NFR-SEC-03).
- **No `innerHTML`/`dangerouslySetInnerHTML`** with user, document or model text. Rich text is `Span[]` (D-028).
- **Honest copy only.** Use the strings in `design.md §9`. Never write "100% on-device", "zero cloud", FERPA,
  or similar (NFR-PRIV-04). A copy-lint test enforces it.
- **No hard-coded metrics** in UI (NFR-FID-07). Demo numbers from Stitch exist only in dev fixtures.
- **No runtime CDN** (fonts, icons, scripts); no telemetry; no network in tests (D-018, D-026, NFR-TEST-02).
- **PyMuPDF is imported only in `apps/server/templix/ingest/native/`** (D-007).
- **Light theme only;** no `dark:` classes, no theme toggle.
- **Pydantic is the schema source of truth;** generated TS/JSON Schemas are committed and checked for
  freshness (D-015). Never hand-edit generated files.
- **Model IDs are data, not code** (D-027).
- **Measure, don't assert:** quality claims need a test or a computed value.

## 4. How you must work

**Process**
1. **Start in plan mode.** Read all docs, then write `PLAN.md`: milestone breakdown with tasks, risks, and
   the questions you need answered. Wait for Yash's approval of the plan before writing code.
2. Work **milestone by milestone** (§6). At the end of each milestone **stop**, run `make check`, update
   `PROGRESS.md`, and give the report in §8. Do not start the next milestone without a go-ahead.
3. Small, reviewable commits (conventional commits). Tests land **with** the code they cover.
4. If you must deviate from a decision or requirement: add a `Proposed` ADR to `docs/decisions.md`
   (`D-031`, …), explain why, and flag it in the milestone report. Do not silently change scope.
5. Questions: only ask for what blocks you; batch them. Defaults for OQ-1…OQ-7 are in `decisions.md` — use
   them unless Yash says otherwise.
6. Prefer boring, well-known solutions. Every new dependency needs an addition-log line in
   `docs/dependencies.md §9` (why, licence, maintenance).

**Quality bar**
- TypeScript `strict`; Python typed (pyright strict); lint clean with zero warnings.
- Definition of Done for any task: code + unit tests + (if UI) component/e2e test + a11y check (axe) +
  docs/ADR updated if behaviour changed + `make check` green.
- Prefer property-based tests for patches, locked-layer integrity and schema round-trips (fast-check,
  hypothesis).
- Performance and fidelity budgets in the NFRs are **gates**, not aspirations.

**Environment bootstrap (do this in M0)**
```
make setup      # corepack enable; pnpm install; uv sync; playwright install chromium
make dev        # runs server (uvicorn --reload) + web (vite) together; prints the one-time URL
make check      # lint + typecheck + unit + schema-freshness + copy-lint + a11y smoke
make e2e        # Playwright (functional + landmark parity + perf budgets)
make fixtures   # generates synthetic fixture PDFs into fixtures/generated/
```

## 5. Repository layout (create exactly this; details in architecture §4)

```
apps/web  apps/server  packages/{doc-schema,render-core,rules,ui}  design/stitch  docs  fixtures  e2e
```
Add: `Makefile`, `.editorconfig`, `.nvmrc`, `.python-version`, `LICENSE` (AGPL-3.0, pending OQ-1),
`PROGRESS.md`, `PLAN.md`, `.github/workflows/ci.yml` (or equivalent), `fixtures/private/` in `.gitignore`.

## 6. Milestones

Each milestone lists deliverables and **acceptance tests** (your report must show them passing).

### M0 — Foundation and design system
**Deliverables:** monorepo scaffold and tooling; Tailwind v4 theme from `design.md §2.4`; fonts/icons
self-hosted; `packages/ui` with every component in `design.md §4` and a `/dev/ui` gallery covering all states;
**App shell** and **Workspace shell**; the six Stitch screens implemented as **static, typed React screens
with fixture data behind a dev flag** (routes in `design.md §8`), applying the corrections in `design.md §12`;
fixture generator (`make fixtures`) producing ≥ 4 synthetic PDFs (single-column text, two-column newsletter
with image + rule + box, image-heavy page, vector-heavy page).
**Acceptance:** landmark-parity tests for the six screens pass (NFR-TEST-04); axe has no serious/critical
violations on all routes (NFR-A11Y-01); copy-lint and no-literal-metrics lints are active and green; contrast
test for all token pairs passes; no external network requests at runtime (Playwright request log).

### M1 — Backend core, data model, security
**Deliverables:** Pydantic domain models (Template, Content, Document, Patch, Rule, Slot, Node types) →
OpenAPI + JSON Schemas → generated TS in `packages/doc-schema` (CI freshness check); SQLite + Alembic + blob
store; session token, Host/Origin checks, security headers (architecture §10.2); `/status`, template/document
CRUD, `/documents/:id/ops` with validation (schema + ownership + size); job runner + SSE; **vault** + provider
config endpoints (write-only key) with a **FakeProvider**; structured redacting logs.
**Acceptance:** API tests for each endpoint; DNS-rebinding/CSRF tests (NFR-SEC-02); redaction test with
key-shaped strings (NFR-SEC-03); `kill -9` fault test (NFR-REL-01); op-apply/invert property tests (NFR-TEST-05);
migration test scaffold (NFR-REL-03).

### M2 — Ingestion (native pass + heuristics)
**Deliverables:** upload validation and sandboxed subprocess (FR-ING-01/02); native extractor behind the
`NativeExtractor` port (text/images/vectors/page boxes, FR-ING-04); reference rasteriser + endpoint; heuristic
roles, reading order, grouping, columns, header/footer, tokens, slots + constraints, font resolver, confidence
and review items (FR-ING-05…13); ingestion job with SSE progress and cancel (FR-ING-03); the **analysis
screen bound to real data** (overlays drawn on the reference raster for now), Home upload flow and template
cards bound to the API.
**Acceptance:** FR-ING-04 character-coverage ≥ 99 % on all fixtures; FR-ING-07 and -08 fixture tests; FR-ING-10
property (original text → zero violations; +30 % → one); malformed/encrypted/oversize fixtures fail cleanly;
sandbox limits proven; NFR-PERF-03 timing on the 2-page fixture (without fidelity yet).

### M3 — render-core, rules, export, fidelity
**Deliverables:** `render-core` (nodes→DOM, text fit modes, font loading, `__templixReady`), font serving,
`rules` package with all kinds (FR-RUL-01), Playwright export job (FR-EXP-01/03), **fidelity scoring** and
diff heatmap (FR-ING-14, architecture §6.5), analysis screen now shows the **reconstruction** plus compare
view (FR-TPL-18).
**Acceptance:** NFR-FID-01 (≥ 0.97 digital-native fixtures, ≥ 0.93 every fixture), NFR-FID-02, NFR-FID-04
(determinism), NFR-FID-05 (preview = export), NFR-PERF-04; rule unit tests (pass/fail per kind); text-fit tests
including the Devanagari fixture if present (record result even if it fails: FR-ING-18 is P2).
**If fidelity is below target:** do not tweak thresholds. Diagnose per page (heatmap), fix extraction/
rendering, and report which fixture features are the cause.

### M4 — Template review and editing
**Deliverables:** FR-TPL-01…13, 17 and FR-MODE-*: layers tree, inspector (editable numerics), direct
manipulation with snapping/keyboard nudge, structure edits, Styles and Rules tabs, **Make repeatable**
(component + repeater), review queue ("Review items", "Accept all detected"), Save as Template with
versioning, mode picker, Templates and Documents list pages, FR-HOME-* complete.
**Acceptance:** every FR-TPL/FR-MODE acceptance criterion; all edits are undoable patches; keyboard-only
path for selecting and nudging a layer (NFR-A11Y-02); fidelity re-score after edits works.

### M5 — Manual Edit
**Deliverables:** FR-MAN-01…15, FR-DOC-01…05, export dialog (FR-EXP-02/04/05), autosave/undo-redo,
selection sync, counters, rich text (Tiptap → `Span[]`), image replace/crop/dpi warning, repeaters,
warnings/auto-fit, grid guides, shortcuts dialog.
**Acceptance:** NFR-PERF-02 (≤ 100 ms p95); NFR-FID-03 (locked-layer integrity property test over random
edit sequences); NFR-REL-01; FR-MAN acceptance criteria; complete e2e: *upload fixture → review → save → create
document → edit headline/body/image/add article → export PDF → verify PDF text and fonts*.

### M6 — Providers, Settings, AI Assist
**Deliverables:** provider adapters (OpenAI, Anthropic, Google, OpenAI-compatible) behind `LLMProvider` with
list-models/test/complete/stream, capability registry, structured-output ladder + repair (architecture §9.2);
Settings (General, AI Models, Fonts, Privacy) per `design.md §8.6`; consent dialog + ledger + indicator
(FR-AI-14, FR-SET-10); deterministic interview planner; slot digest; patch contract + server allow-list;
streaming proposals; **fit loop**; Proposed Changes UI and diff highlight; free-form edit commands; usage
readouts.
**Acceptance:** all AI tests use the **FakeProvider** (no network): NFR-COST-01 (one-word edit ≤ 3 k input
tokens, 1 call), NFR-COST-03 (stable prefix), NFR-SEC-07 (≥ 25 adversarial prompt-injection cases rejected or
neutralised), NFR-PRIV-01/02/03 (zero egress before consent; ledger completeness), key never appears in any
response/log; manual smoke test with a real key documented in `docs/manual-qa.md` (do not commit keys).

### M7 — Hardening and release
**Deliverables:** accessibility pass (NVDA/VoiceOver notes), performance budgets (NFR-PERF-*), fault/chaos
tests (NFR-REL-05), OS matrix CI (Windows first), real-reference tuning with Yash's private corpus, README
quick-start, `THIRD_PARTY_NOTICES.md`, About dialog data, diagnostics bundle, `make run` production-like
start, security review checklist (architecture §10 table T1–T9 each with evidence).
**Acceptance:** all gates in the NFRs green or explicitly waived in an ADR; a new user completes NFR-USA-01 in
a recorded session.

## 7. Implementation guidance (the hard parts)

- **Coordinates:** convert PDF space to top-left/y-down once at the extractor boundary. Everything downstream
  uses points, top-left origin (architecture §5.2).
- **Text spans → text nodes:** merge spans on the same baseline into lines, lines into blocks using font,
  size, colour and gap thresholds; keep per-run style so mixed bold/italic survive (runs).
- **Fonts:** strip PDF subset prefixes (`ABCDEF+`), build a font index, resolve with certainty; unresolved →
  review item, never silent substitution (NFR-FID-06). Subset fonts embedded in PDFs are not reused.
- **Fit:** measure in the browser only; wait for `document.fonts.ready`; the server never measures text.
- **Patches:** one mechanism for undo/redo, autosave, section history and AI proposals (D-016). Validate on
  the server; do not trust the client or the model.
- **AI structured output:** use the ladder (native schema → tool → json_object → text+repair). Never `eval`.
  Put stable content first in prompts; log token counts; keep digests small (architecture §9.4).
- **Security:** token + Host/Origin checks on every request; CSP; subprocess sandbox for PDFs; SSRF rules for
  the custom base URL (T6). Write the security tests **before** the endpoints.
- **Performance:** virtualise long lists; avoid re-rendering the whole page on each keystroke (render only the
  affected node subtree); debounce measure-based rules; use `content-visibility` for off-screen pages.
- **Stitch parity:** copy structure, spacing and tokens, not code. Fix the defects in `design.md §12`
  (clipping, wrapping, toolbar overlap, dishonest copy, hard-coded data) as you build — they are requirements.
- **Fixtures:** generate synthetic PDFs by script (reportlab dev-dependency) to cover: single/multi-column,
  images, vectors, rules, boxes, running header/footer, Devanagari, missing font, scanned (image-only),
  malformed, encrypted. Real documents Yash provides go to `fixtures/private/` (git-ignored); never upload
  them anywhere and never include them in logs or test artifacts.

## 8. Milestone report format (end of every milestone)

1. **What was built** (5–10 bullets, mapped to FR/NFR ids).
2. **Evidence:** exact commands run and results (`make check`, `make e2e`, fidelity scores, perf numbers,
   screenshots of parity artifacts).
3. **Deviations/ADRs** added or proposed.
4. **Known gaps / risks** (honest list; include any failing gate and why).
5. **Questions** for Yash (batched) and the proposed next milestone.

## 9. Things you must not do

- Do not copy Stitch `code.html` into the app or use the Tailwind CDN script.
- Do not add dark mode, accounts, cloud sync, telemetry, analytics, or hosted-OCR calls.
- Do not store or log API keys, prompts, or document text (default log level).
- Do not let a model or a user string reach the DOM as HTML.
- Do not hard-code model names, quality scores, confidence values, RAM/latency/cost numbers.
- Do not lower thresholds to make tests pass; fix the cause or report it.
- Do not introduce a second renderer, a second schema definition, or a second rules engine.
- Do not mark a milestone done with failing gates or skipped tests; mark `xfail` only with a linked ADR.
- Do not proceed past a milestone boundary without Yash's go-ahead.

## 10. First actions (now)

1. Read the documents listed in §1 and open all six `design/stitch/*/screen.png`.
2. Write `PLAN.md` (milestones, task breakdown, risks, assumptions, questions). Include a short list of any
   contradictions or ambiguities you found in the specs.
3. Ask Yash the batched questions (defaults are in `decisions.md`; especially OQ-1 licence, OQ-2 sample PDFs,
   OQ-3 operating system) and **wait for approval** before starting M0.
