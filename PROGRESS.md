# Progress

## Status: M2 + a narrow manual end-to-end slice committed on main, unapproved (2026-10-23)

The baseline audit (`docs/audits/engineering-baseline-audit-v2.md`) recorded the previous ambiguity: this
file said "M1 complete, awaiting approval" while a substantial M2 tree existed uncommitted. That tree is
now committed in reviewable slices on `main`, but M2 is **not approved**. M3 (the full
renderer/rules/fidelity milestone) has not started; a narrow manual text-edit/export slice is committed
on top of M2.

### 2026-10-23 — Manual vertical slice (committed, interim)

Goal: upload PDF → analysis → create document → edit text → export PDF, without claiming M3.

- New documents now prefill `content.values` from the first bound template node's runs, so the editor
  starts with the source content instead of blank slots.
- `GET /api/v1/documents/{id}/export.pdf` runs a PyMuPDF export worker inside the ingest sandbox
  (D-007 boundary preserved). It redacts only changed text frames, preserves images/rules, and redraws
  replacement text in the original frame. This is an **interim FR-EXP-01 path, not the M3 renderer**.
  If replacement text cannot fit even at 6 pt, export returns `422 text_overflow` instead of a PDF
  with silently missing text.
- Live `/documents/:id/manual` editor: page reference, slot overlays, debounced serialized autosave
  through the op log, retry on save failure, and PDF export. `/documents` lists drafts so they reopen.
- Live Analysis now offers **Edit content**, creating a prefilled draft and navigating to the editor.
- Fixed two M2 defects found by visual export checks: a y-coordinate flip in the export overlay and
  template tokens being built before node style refs existed (tokens were empty).
- Evidence: pytest **146**, vitest **31**, fixture e2e **15/15**, live e2e **3/3**, eslint/tsc/ruff/pyright
  clean.
- `npm run check` is green, including schema freshness, now that the generated `packages/doc-schema`
  files are committed.
- Limits: text-only export; Base14 fonts, so non-Latin text may not render; multi-column text is split
  approximately; images are preserved but not replaceable; rotated pages are unverified; no undo/redo,
  rules, or fidelity scoring. Full v1 remains deferred.

### 2026-10-23 — Live-flow fixes

- `/api/v1/status` now returns `engine`, `version`, `parser`, `ram` (null until measured), and
  `privacyMode` (FR-SYS-02). Live Home/Analysis use it instead of fixture identity/status (F-03).
- Op-log 500 fixed: `invert_patch` is inside the `ValueError` guard, so malformed owned patches return
  422. Regression tests cover a non-list `set_slot` value and a double `clear_slot` (F-04).
- Live "Next: Choose Mode" dead end removed; live analysis now offers **Edit content** for the manual editor (F-07).
- Added a cancel control during ingestion, and an early-SSE-failure path that no longer hangs at 0% (F-10/11).
- Exposed the page-limit override as an upload checkbox; `uploadPdf` sends `allowManyPages` (F-09).
- Fixed the live e2e harness: `apps/web/.env.development` was forcing fixture mode in the "live" run, and
  the fixture suite could reuse an unrelated app on port 5173. Fixture e2e now uses a dedicated port
  (`E2E_WEB_PORT`, default 5175 in `scripts/e2e.ps1`).
- Evidence: live e2e **2/2 passed** (previously never actually live), fixture e2e **15/15**, pytest **134**,
  vitest **19**, eslint/typecheck/ruff/pyright clean.

### 2026-10-23 — P1 evidence: CI, docs, frontend tests

- `.github/workflows/ci.yml`: one `gate` job runs eslint, 5x tsc, vitest, ruff, pyright, pytest,
  schema freshness, fixture e2e, and live e2e on `ubuntu-latest`. The first green run is triggered by
  this push; confirm it on GitHub.
- `README.md` (quick-start, layout, gates, security, licence) and `apps/server/README.md`
  (satisfies the `readme` field in `pyproject.toml`).
- `THIRD_PARTY_NOTICES.md` covers runtime web/server dependencies, fonts, and the PyMuPDF
  AGPL-or-commercial notice.
- `docs/licensing.md` no longer claims PyMuPDF is unused; the note now records the real import and
  that OQ-1 is still unconfirmed.
- `apps/web/tests/liveScreens.test.tsx` adds 6 tests: empty live Home, unreachable-server banner,
  page-limit upload override, analysis layer/review rendering, analysis load failure, and
  cancel + early-SSE-death handling.
- Sandbox memory cap now proven: `test_ingest.py::test_sandbox_memory_cap_is_enforced` runs an
  uncapped control (allocates) and a 64 MB-capped child (`MemoryError`, no output).
- 20-page performance proof: `test_api_ingest.py::test_20_page_ingest_under_45s` (NFR-PERF-03 release
  half, full upload → job → analysis).
- RFC 7807 error contract: all HTTP failures return `application/problem+json` with `code` + `hint`;
  the SPA renders `hint` instead of a JSON blob.
- Dependency audits are clean (`pnpm audit`, `pip-audit`), both wired into CI. Coverage is
  **91.7%** overall; CI enforces a 60% floor (NFR-MAINT-03).
- Layer counts now recurse through nested groups in both the API and live Analysis; FR-SYS-01 uses
  the copy deck's "LOCAL APP" label.
- Job history is bounded at 100 terminal jobs (oldest pruned); restart persistence/interrupted state
  remains open (NFR-REL-04).
- Irregular-table validation is explicitly deferred (D-033) until FR-ING-20 table detection exists.
- Evidence: vitest **27 passed** (was 19), pytest **139 passed** (was 134), eslint clean,
  `tsc -p apps/web` clean, ruff/pyright clean.
- **M2 acceptance package:** `docs/reports/m2-ingestion-report.md` follows the AGENT_PROMPT §8 report
  format (built scope, evidence table, deviations, gaps, owner questions).

Still open before M2 approval: owner review/approval of the committed slices, the D-007/OQ-1
(PyMuPDF/AGPL) decision, the first green CI run, and NFR-TEST-04 parity enforcement (still
scaffold-only).

### M1 — Backend core, data model, security

- **Domain models (D-015):** Pydantic v2 in `apps/server/templix/model/` — Template/Content/Document,
  Page/Node/Slot/Rule/Section/Fidelity, Patch/Ops with apply + invert, strict (extra="forbid") models.
- **Schema pipeline:** `uv run python -m templix.model.generate` writes JSON Schema + OpenAPI
  (`packages/doc-schema/schema/*.json`) and generated TypeScript (`packages/doc-schema/src/index.ts`) in one
  deterministic pass (LF, no timestamps). `scripts/check.ps1` step 5 regenerates and diffs → freshness gate.
- **Persistence:** SQLite WAL + SQLAlchemy Core (`templix/store/`), content-addressed blob store (sha256,
  2-char sharding, idempotent puts), Alembic scaffold + initial migration with pre-upgrade backup
  (NFR-REL-03), kill-9/WAL recovery test (NFR-REL-01).
- **Security (architecture §10.2):** session cookie + launch token, Host/Origin checks (DNS-rebinding +
  CSRF, NFR-SEC-02), security headers, constant-time token compare.
- **API:** `/status`, `/session`, template CRUD, document CRUD, `/documents/:id/ops` (schema + ownership +
  size limits: ≤1000 ops, ≤128 KiB), job runner with SSE `GET /jobs/:id/events`, provider endpoints
  `PUT/GET/DELETE /providers/{name}/key` (write-only, masked hint).
- **Vault (D-010, NFR-SEC-03):** `templix/vault` (`KeyringStore` on `keyring`, `MemoryStore` for tests) +
  `templix/provider.FakeProvider` (offline, deterministic). Keys never in DB, logs, responses.
- **Logs:** stdlib `logging` with JSON formatter + idempotent secret-redaction (NFR-OBS-01), key-shaped
  strings covered by tests.
- **Deviations (Proposed ADRs):** D-031 (Python generator renders the TS, not `openapi-typescript`),
  D-032 (job handlers run inline in M1; background execution is M2's first task).
- **Dependencies:** 7 added this milestone, logged in `docs/dependencies.md §9` (NFR-SEC-08); 6 planned
  packages avoided by using the stdlib (noted in that log).

### M1 gates (historical)

- `scripts/check.ps1`: eslint (code + copy-lint + no-literal-metrics), typecheck (5 tsconfigs), ruff +
  pyright strict, 15 vitest, 46 pytest, schema freshness — all green in the final M1 run.
- `apps/server`: `uv run ruff check .` → 0; `uv run pyright .` → 0; `uv run pytest -q` → 46 passed.

### Open / unverified

- Landmark/pixel parity numeric comparison vs Stitch (from M0) — pending visual sign-off; issue #9 in the
  audit is still scaffold-only.
- `httpx2` (dev) was added for starlette's `TestClient`; confirm it as test tooling (M1 report Q).

### Next (owner-gated)

1. Resolve D-007/OQ-1 (PyMuPDF/AGPL) and the distribution decision.
2. Review and approve the committed M2 + manual-slice slices.
3. Confirm the first CI run on GitHub and fix any failures.
4. Implement NFR-TEST-04 landmark comparison; it still needs the Stitch mapping sign-off.
5. Only then start M3 (render-core, rules, full export, fidelity). The manual slice is useful today but
   is not a substitute for M3 acceptance.
