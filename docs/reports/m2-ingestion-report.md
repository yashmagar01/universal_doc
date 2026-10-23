# M2 — Ingestion milestone report

**Status: implemented and committed on `main` in reviewable slices, NOT approved.** M3 has not
started. A narrow manual text-edit/export slice is committed on top of M2; see `PROGRESS.md`; it is
not M3.

Date: 2026-10-23 · Evidence source: local gate runs on Windows · Audit:
`docs/audits/engineering-baseline-audit-v2.md`

## 1. What was built

- **Upload validation and sandboxed parsing (FR-ING-01/02).** `POST /api/v1/templates/ingest` checks the
  `%PDF` magic and the 50 MB cap before storing a blob; the worker runs in a subprocess with a wall-clock
  limit, Windows Job Object / POSIX `RLIMIT_AS` memory cap, output cap, and kill-on-cancel
  (`ingest/sandbox.py`, `ingest/validate.py`, `ingest/native/`).
- **Native extractor behind the `NativeExtractor` port (FR-ING-04).** PyMuPDF is imported only inside
  `ingest/native/`; it emits spans, images, vectors, page boxes, fonts, and 150 dpi reference rasters.
  `GET /templates/{id}/pages/{index}/reference.png` serves the raster.
- **Heuristics (FR-ING-05/06/09/11/12).** Roles, reading order, grouping, columns/gutters,
  running header/footer detection, palette/spacing tokens, style book, and confidence per node/page.
- **Slots and measured constraints (FR-ING-08/10).** Shared headers/footers/titles collapse into one slot
  across pages; constraints come from the original text (`maxChars`, `maxLines`, `charsPerLine`).
- **Font resolution (D-018).** Deterministic cascade (system → bundled → alias/fuzzy) with source and
  certainty recorded per node; unresolved fonts become review items.
- **Validators and review items (FR-ING-13).** Clipping, overlap, contrast, image DPI, orientation, and
  font substitution produce stable `ReviewItem` ids (`kind-###`) with confidence.
- **Ingestion job with SSE and cancel (FR-ING-03).** `POST /templates/ingest` → job → SSE
  `GET /jobs/{id}/events` (validate 5 %, extract 30 %, build 60 %, save 95 %) → `done`; cancel kills the
  worker and marks the job cancelled; failures are job states, not server faults.
- **Live Home and Analysis.** Home lists templates from `GET /templates`, uploads with the page-limit
  override, and shows `/status` facts. Analysis streams progress, shows overlays on the reference raster,
  groups review items, cancels, and fails visibly instead of hanging at 0 %.
- **P1 audit fixes are included:** `/status` contract, op-log 422, live identity/status, Mode dead-end
  removal, page override, early-SSE failure, cancel control, CI, README/notices, frontend live tests.
- **RFC 7807 errors (P2 #16).** Every HTTP failure is `application/problem+json` with `code` + `hint`
  (`api/problems.py`); the SPA shows the hint instead of a JSON blob.

## 2. Evidence

Commands and results from the latest runs:

| Command | Result |
|---|---|
| `uv run pytest -q` (apps/server) | **146 passed** |
| `uv run --with pytest-cov pytest --cov=templix` | **91.7%** overall (CI floor 60%) |
| `pnpm audit --audit-level high` | no known vulnerabilities |
| `uv run --with pip-audit pip-audit --local` | no known vulnerabilities |
| `npx vitest run` | **31 passed** (4 files) |
| `E2E_WEB_PORT=5175 npx playwright test` (e2e) | **15 passed** (fixture suite) |
| `npx playwright test -c playwright.live.config.ts` (e2e) | **3 passed** (real API + live Vite) |
| `npx eslint . --no-warn-ignored` | 0 problems |
| `npx tsc --noEmit -p <workspace>` ×5 | clean |
| `uv run ruff check .` | clean |
| `uv run pyright .` | clean |
| `npm run check` | **green**, including schema freshness |
| `git diff -- packages/doc-schema` after regeneration | current (matches generator) |

Acceptance mapping:

| Acceptance criterion | Test evidence | Status |
|---|---|---|
| FR-ING-04 character coverage ≥ 99 % on every healthy fixture | `test_ingest.py::test_char_coverage` (5 fixtures, parametrized) | Pass |
| FR-ING-07/08 roles, columns, furniture, shared slots | `test_heuristics.py`, `test_pipeline.py`, `test_slots.py` | Pass |
| FR-ING-10 original text passes; +30 % violates | `test_slots.py::test_original_passes_and_thirty_percent_fails`, `test_pipeline.py::test_thirty_percent_longer_violates` | Pass (example-based) |
| Malformed / encrypted / oversize fail cleanly | `test_api_ingest.py::test_malformed_upload_fails_job`, `test_job.py::test_ingest_job_fails_cleanly_on_encrypted`, `test_ingest.py::test_validate_rejects_oversize` | Pass |
| Sandbox wall-clock and cancel | `test_ingest.py::test_sandbox_wall_clock_kills_worker`, `test_sandbox_cancel_kills_running_child` | Pass |
| Sandbox memory cap | `test_ingest.py::test_sandbox_memory_cap_is_enforced` (uncapped control allocates; a 64 MB cap produces `MemoryError` before the allocation prints) | Pass |
| NFR-PERF-03: 2-page fixture ≤ 10 s | `test_api_ingest.py::test_upload_ingest_analysis_roundtrip` | Pass |
| NFR-PERF-03: 20-page PDF ≤ 45 s | `test_api_ingest.py::test_20_page_ingest_under_45s` (10× the 2-page fixture, full upload → job → analysis) | Pass |
| RFC 7807 errors with `code` + `hint` | `test_api.py::test_http_errors_use_problem_details`, `test_api_ingest.py::test_non_pdf_rejected_before_job` | Pass |
| NFR-SEC-08: no unwaived high/critical dependency findings | `pnpm audit` and `pip-audit` locally; both are CI steps | Pass (local) |
| NFR-MAINT-03: overall coverage ≥ 60% | 91.7% measured; CI enforces 60% | Pass |
| Job history stays bounded | `test_job.py::test_runner_bounds_terminal_job_history` (oldest terminal job pruned at 100) | Pass |
| Live ingest journey (upload → SSE → analysis → issues) | `e2e/live/ingest.spec.ts` | Pass (3/3) |
| Reference raster is a real image | `test_api_ingest.py::test_reference_raster_served`, live e2e `naturalWidth > 0` | Pass |
| PyMuPDF import boundary (D-007) | `test_ingest.py::test_pymupdf_stays_inside_native_boundary` | Pass |
| Schema freshness | Generator output current; `scripts/check.ps1` step 5 stays red by construction until the tree is committed | Partial |

## 3. Deviations and ADRs

- **D-031** — Python generator renders the TypeScript schema instead of `openapi-typescript` (accepted).
- **D-032** — job handlers run on daemon threads, not a process pool; the sandbox subprocess provides the
  isolation that matters for hostile PDFs. The architecture doc still says `ProcessPoolExecutor` (audit D-04).
- **D-007/OQ-1** — PyMuPDF is imported and used under the provisional AGPL assumption. The owner decision
  is still open; `docs/licensing.md` and `THIRD_PARTY_NOTICES.md` now record the real state.
- **Page-limit override** — the UI checkbox reaches the API, but `MANY_PAGES = 100000` makes the overlay a
  de-facto no-limit rather than the spec's 100-page ceiling (audit D-08). Needs an owner call.
- **`rapidfuzz` floor** — changed from `==3.14.1` to `>=3.14.1` to match the floor policy in
  `docs/dependencies.md`; the lockfile still resolves 3.14.1 (P3 resolved).
- **`ram` in `/status` is `null`** — no probe is installed, so the UI shows “—” rather than inventing a
  number. This is deliberate honesty, not a rendering bug.

## 4. Known gaps and risks

- **M2 is committed but unapproved.** Owner review/approval of the reviewable slices remains required;
  otherwise status and rollback still need an explicit acceptance decision (audit R-01).
- **CI is authored; this push triggers its first run.** `.github/workflows/ci.yml` is committed; confirm
  the first green run on GitHub and fix any failures (audit R-05).
- **NFR-TEST-04 parity is still capture-only.** No geometry tolerance comparison; needs the Stitch mapping
  sign-off (audit R-06).
- **Early-allocation race.** The Windows Job Object is assigned just after `Popen`, so a child that
  allocates gigabytes in its first milliseconds can briefly exceed the cap (documented in
  `ingest/sandbox.py`). The test proves the cap for normal allocation; closing the race needs a
  suspended-start/assign/resume sequence if it ever matters.
- **Orphan blobs.** A failed/cancelled upload leaves the content-addressed blob because deletion could race
  a shared reference; no retention job exists yet (audit R-12).
- **In-memory job history.** Terminal jobs are capped at 100; events live with the job until it is
  pruned. Jobs do not survive a server restart, so NFR-REL-04's `interrupted` state and retry path
  remain open (audit R-11).
- **Irregular-table validation is explicitly deferred (D-033).** FR-ING-13 lists it, but no table
  detector exists yet (FR-ING-20, P2), so there are no `table` nodes to validate. Revisit when table
  detection lands.
- **Full requirements traceability matrix** (audit P2 #20) is not written; the M2 acceptance mapping
  above is the current trace for this milestone.
- **Missing fixture categories.** No Devanagari, scanned/image-only-with-OCR-target, or missing-font
  fixture; FR-ING-18 remains P2 (audit R-16).
- **Coverage floors for future packages.** Overall coverage is measured at 91.7% and CI enforces 60%;
  the NFR's 80% floors for `render-core`, `rules`, `ai/patches`, and `ingest/fuse` cannot be measured
  until those packages exist.
- **About dialog absent.** README/notices exist; NFR-LIC-01's in-app licence surface is M7.
- **M3 not started.** `packages/render-core` and `packages/rules` remain placeholders.

## 5. Questions for the owner

1. **D-007/OQ-1:** accept AGPL obligations, buy a commercial PyMuPDF licence, or swap the extractor
   (`pypdfium2` + `pdfminer.six`)? Distribution model (private/internal vs public binary) decides the rest.
2. **M2 approval:** is the evidence above sufficient, with the parity gap and early-allocation race
   recorded?
3. **Commit split:** committed as (a) backend + tests, (b) live web + tests, (c) e2e, (d) CI, and
   (e) docs/status. Confirm that split is acceptable for review.
4. **Page-limit ceiling:** keep the spec's 100-page override, or document “no practical limit”?
5. **Parity sign-off:** who maps Stitch landmarks to `data-qa` regions, and against which PNGs?

**Proposed next step:** review/approve the committed slices, confirm the first CI run on GitHub, then
close M2 and start M3 only with explicit approval. Any parity or memory-cap work stays visible as open
P2 items rather than being silently skipped.
