# Templix Engineering Baseline Audit v2

| Field | Value |
|---|---|
| Audit date | 2026-10-20 |
| Repository | `C:/Users/Yash/OneDrive/Desktop/Templix` |
| Branch / baseline | `main`; commit `7e772a9` plus uncommitted working tree |
| Scope | Repository, documentation set, M0-M2 implementation, quality gates, release readiness |
| Mode | Read-only audit. Only this report was created. |
| Evidence cut-off | Local commands run on 2026-10-20; no CI results, no live end-to-end run |
| Overall confidence | High for code/tests read and run; medium for milestone status; low for effort/timeline |

This audit treats the **current working tree** as the baseline. Uncommitted M2 work is real code, but it is not part of any reviewed commit or approved milestone. It is therefore assessed separately from the committed M0/M1 history.

---

## 1. Executive summary

Templix is a credible local-first prototype. The backend has a coherent domain model, a security baseline that is better than typical for this stage, and a substantial pytest suite. M0 screens exist and pass accessibility checks. M1 is committed and its core API/security tests pass. M2 is materially implemented, including a working PyMuPDF extraction pipeline, sandbox, heuristics, slots, validators, and live Home/Analysis wiring.

The project is **not release-ready**, and it is **not at a clean milestone gate**. The dominant problems are process and evidence gaps rather than missing ambition:

- M2 work is uncommitted and was started while `PROGRESS.md` still says M1 complete, awaiting owner approval.
- No CI exists, no README exists, and no standalone milestone reports were found.
- The visual-parity test captures screenshots and landmark boxes but explicitly does not enforce the NFR-TEST-04 tolerance.
- Live Home and Analysis still display fixture identity and fixture status values; the live `/status` endpoint does not supply the contract that FR-SYS-02 requires.
- A malformed-but-owned document op causes an unhandled exception and a 500 instead of a 422 (confirmed by reproduction).
- The live Analysis Next: Choose Mode action leads to a fixture-gated Mode screen that rejects real template ids.
- Frontend verification is thin: 15 Vitest tests, all in `packages/ui`; no `apps/web` component tests; live e2e is blocked by a pre-existing server on port 8000.

**No confirmed P0 defect was found in local-only execution.** The highest-severity findings are P1 because they block a defensible milestone/release gate, not because they destroy data or expose the host. If distribution is intended, the unresolved PyMuPDF/AGPL decision becomes a release blocker of the highest order.

| Verdict area | Verdict |
|---|---|
| Local demo | Usable with caveats |
| M0 gate | Substantially met; parity acceptance not actually enforced |
| M1 gate | Code present and tested; approval/report evidence missing; `/status` contract partial |
| M2 gate | Not met; unapproved, uncommitted, live e2e unverified, acceptance gaps |
| Release readiness | Not ready |
| Security baseline | Good local-only baseline; no P0 found; hardening/CI still needed |
| Documentation | Strong specification set; missing README/reports/traceability and some stale claims |

### Top findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | P1 | M2 proceeded without the owner gate and is not committed | `PROGRESS.md:3-6`; `PLAN.md:20-22`; 18 modified + 27 untracked entries |
| F-02 | P1 | Licensing decision is still provisional while PyMuPDF is now imported; notices/README/About are incomplete | `docs/decisions.md` D-007/OQ-1; `docs/licensing.md`; `ingest/native/pymupdf_native.py`; `LICENSE` present, `THIRD_PARTY_NOTICES.md` absent |
| F-03 | P1 | Live screens show fixture identity/status instead of live values | `HomeLive.tsx`; `Home.tsx:52-83`; `AppShell.tsx:29-32`; `/status` returns only `schemaVersion` + `state` |
| F-04 | P1 | Malformed owned op returns 500 | `api/routes.py` `documents_ops`; `model/patch.py` `invert_patch`; reproduced |
| F-05 | P1 | No CI and no enforced release gate | `.github/` absent; local scripts only |
| F-06 | P1 | NFR-TEST-04 parity is scaffold-only | `e2e/parity/parity.spec.ts:9-11` |
| F-07 | P1 | Live Analysis CTA dead-ends at fixture Mode screen | `AnalysisLive.tsx` -> `/templates/{id}/mode`; `ModePicker.tsx:14` |
| F-08 | P1 | Frontend test coverage is effectively absent | 2 Vitest files, both in `packages/ui`; no `apps/web/tests` |
| F-09 | P2 | Page-limit override is unreachable in the UI and unlimited in the worker | `ingest/job.py` `MANY_PAGES = 100000`; `api.ts` `uploadPdf` sends no flag |
| F-10 | P2 | Cancel is API-only; no cancel control during ingestion | `AnalysisLive.tsx` progress card |
| F-11 | P2 | SSE early failure can leave the analysis screen stuck | `AnalysisLive.tsx` `onerror` + suppressed 404 |
| F-12 | P2 | Error contract is not the documented RFC 7807 shape | `docs/system-architecture.md` section 11; `api/routes.py` |
| F-13 | P2 | Sandbox memory cap and real cancellation are not proven by tests | `test_ingest.py` wall-clock/cancel only; no memory test |
| F-14 | P2 | Failed/cancelled uploads leave unreferenced blobs | `templates_ingest` stores blob before job; no cleanup |
| F-15 | P3 | Dependency policy says floors, manifest uses `rapidfuzz==3.14.1` | `docs/dependencies.md:8`; `apps/server/pyproject.toml:17` |

---

## 2. Git and repository evidence

### 2.1 Commit history

| Commit | Date / time | Subject | Evidence note |
|---|---|---|---|
| `9d0d243` | 2026-10-18 | spec import | Initial specification import |
| `3b228f2` | 2026-10-18 06:25:34 +0530 | restructure | Six spec files moved to `docs/` |
| `fef0efd` | 2026-10-18 08:49:22 +0530 | M0 | Foundation/design system |
| `c5c68cf` | 2026-10-18 14:18:50 +0530 | M1 | Backend core/data/security |
| `7e772a9` | 2026-10-18 16:06:24 +0530 | M2 groundwork | 17 files, +451/-142 |

- Branch: `main` only.
- Tags: none.
- Remote/review state: no evidence of pull requests or review.

### 2.2 Working tree

| Item | Value |
|---|---|
| Porcelain entries | 45 total |
| Modified tracked files | 18 |
| Untracked entries | 27 |
| Diff size | 644 insertions, 25 deletions |
| `7e772a9` size | 17 files, +451/-142 |

The untracked set is not incidental. It includes the M2 ingest package and tests:

- `apps/server/templix/ingest/`: `__init__.py`, `pipeline.py`, `job.py`, `sandbox.py`, `validate.py`, `errors.py`, `heuristics.py`, `validators.py`, `slots.py`, `tokens.py`, `fonts/`, `native/`
- `apps/server/templix/serve.py`
- Nine M2 test modules: `test_api_ingest.py`, `test_fonts.py`, `test_heuristics.py`, `test_ingest.py`, `test_job.py`, `test_pipeline.py`, `test_slots.py`, `test_tokens.py`, `test_validators.py`
- `apps/web/src/lib/api.ts`, `apps/web/src/screens/HomeLive.tsx`, `apps/web/src/screens/AnalysisLive.tsx`
- `docs/licensing.md`
- `e2e/live/`, `e2e/playwright.live.config.ts`
- `apps/web/tsconfig.tsbuildinfo` (generated artifact)

### 2.3 Repository readiness

| Artifact | Present | Evidence |
|---|---|---|
| `LICENSE` | Yes | AGPL-3.0 text |
| `README.md` | **No** | Root and `apps/server/README.md` absent |
| `THIRD_PARTY_NOTICES.md` | **No** | Root absent |
| `.github/` / CI | **No** | Absent |
| `docs/audits/` | **No** | Created only for this report |
| `apps/web/tests/` | **No** | No frontend test directory |
| `docs/requirements-traceability.md` | **No** | No traceability file |
| Milestone reports | **No standalone file found** | Only `PROGRESS.md` claims |

This matters because `AGENT_PROMPT.md` section 5 requires `README`, CI, and a repository layout with `.github/workflows/ci.yml`; `apps/server/pyproject.toml` declares `readme = README.md`, and the Makefile says see README while no README exists.

### 2.4 Evidence limits

- Commit timestamps prove ordering, not effort. All five commits are dated the same day.
- The dirty tree cannot be attributed to a specific commit, review, or approval.
- There is no time tracking, issue tracker export, or review log in the repository.
- `test-results/` and `artifacts/parity/` are ignored run artifacts; they are not a durable test record.

---

## 3. Milestone status M0-M7

Status vocabulary: Implemented and verified / Implemented but insufficiently verified / Partially implemented / Planned but not implemented / Blocked / Unknown.

| Milestone | Planned scope | Evidence found | Status | Gate / gap |
|---|---|---|---|---|
| M0 Foundation and design system | Monorepo, theme, UI kit, six static screens, fixtures, a11y, no-network, parity | Six design routes plus dev/404; 8-route axe run passes; 15 fixture e2e tests pass; UI contrast/counter tests pass | **Implemented but insufficiently verified** | Parity test does not compare geometry; visual sign-off still pending per `PROGRESS.md` |
| M1 Backend core, data model, security | Models, schema generation, SQLite/Alembic/blobs, session/Host/Origin, API, jobs/SSE, vault, logs | Committed `c5c68cf`; 132 pytest includes M1 suites; API/security/migration/crash/redaction tests pass | **Implemented but insufficiently verified** | No CI; schema-freshness gate not rerun; `/status` contract partial; not every endpoint has a success-path test; no standalone M1 report; approval not evidenced |
| M2 Ingestion | Upload validation, sandbox, native extractor, heuristics, slots, review items, SSE/cancel, live Home/Analysis | Full pipeline present; 7 PDF fixtures; 132 pytest; live e2e tests written but not run; live Home/Analysis wired | **Partially implemented / insufficiently verified** | Unapproved and uncommitted; no M2 report; cancel UI absent; page override UI absent; fidelity is M3; live status/identity still fixture-backed; live e2e blocked |
| M3 render-core, rules, export, fidelity | Renderer, rule kinds, export, fidelity score/heatmap | `packages/render-core` and `packages/rules` are placeholder `index.ts` files; no fidelity/export implementation | **Planned but not implemented** | Correctly deferred; M2 code must not be presented as M3-complete |
| M4 Template review/editing | Layers tree, inspector, direct manipulation, rules/styles tabs, repeaters, lists, Home complete | Live Analysis shows layers/review items, but Mode screen and editor/list screens are fixture-gated; `/templates` and `/documents` routes do not exist | **Planned but not implemented** | Live Analysis CTA currently dead-ends |
| M5 Manual Edit | Live document editor, autosave/undo/counters/rich text/export | `ManualEditor.tsx` uses `fixtureManualDoc`; no live `GET /documents/{id}` binding or op UI | **Planned but not implemented** | Static screen only |
| M6 Providers, Settings, AI Assist | Real adapters, consent/ledger, interview, patch contract, fit loop | `FakeProvider` and vault exist; Settings and AI Assist are fixture-only; no real provider adapters | **Partially scaffolded** | Only offline seam exists |
| M7 Hardening and release | A11y pass, perf/chaos, OS CI, README, notices, About, diagnostics, packaging | None of the release artifacts exist; server is a dev entry point | **Planned but not implemented** | Release blockers unresolved |

### 3.1 Gate compliance

`PLAN.md` owner condition 1 is explicit: each milestone starts only after the prior milestone is complete, `make check` is green, `PROGRESS.md` is updated, and the milestone report is delivered with evidence.

| Gate | Required | Observed |
|---|---|---|
| M0 -> M1 | `make check`, PROGRESS update, report, owner approval | M0 approved per `PLAN.md`; report not found |
| M1 -> M2 | Same, plus owner go-ahead | `PROGRESS.md` says awaiting approval; M2 exists and was started |
| M2 -> M3 | Same, plus M2 acceptance | M2 has no PROGRESS entry, no report, no approval |

The repository therefore has a **documented gate process that the working tree does not currently satisfy**.

## 4. Timeline and confidence

| Date / time | Event | Evidence | Confidence |
|---|---|---|---|
| 2026-10-18 | Specification imported | `9d0d243` | High |
| 2026-10-18 06:25:34 | Repository restructured | `3b228f2` | High |
| 2026-10-18 08:49:22 | M0 committed | `fef0efd` | High |
| 2026-10-18 14:18:50 | M1 committed | `c5c68cf` | High |
| 2026-10-18 16:06:24 | M2 groundwork committed | `7e772a9` | High |
| 2026-10-20 | Audit baseline; tests/gates run | This report | High |

Observation: M1 followed M0 by 5h29m; the M2 groundwork commit followed M1 by 1h47m. These intervals describe commit ordering only. They are **not** evidence of elapsed engineering effort, team size, or cost. No audit conclusion should infer hours or rates from them.

`PROGRESS.md` is internally time-stamped 2026-10-18 and says M1 is awaiting approval. `PLAN.md` still says Current milestone: M0. The docs therefore do not describe a single consistent project state.

---

## 5. Documentation discrepancy register

| ID | Sources in conflict | Conflict | Impact | Resolution / owner |
|---|---|---|---|---|
| D-01 | `Makefile`, `apps/server/pyproject.toml` vs filesystem | README is referenced but absent | Packaging metadata is broken; onboarding has no quick-start | Create README before M2 approval |
| D-02 | `PROGRESS.md:3` vs working tree | M1 complete/awaiting approval vs substantial M2 work | Gate breach and unclear status | Freeze, report, approve M2 explicitly |
| D-03 | `docs/decisions.md:51` and `:332` vs `PROGRESS.md` | D-032 is Accepted but listed under Deviations (Proposed ADRs); D-032 references nonexistent D-034 | Decision log is not trustworthy as an index | Add D-034 or remove the reference; move D-032 |
| D-04 | `docs/system-architecture.md:504` vs `api/jobs.py` | Architecture says `ProcessPoolExecutor`; implementation uses daemon threads | Reviewers may assume CPU isolation that is not there | Record thread choice as an explicit architecture amendment |
| D-05 | `docs/system-architecture.md:464,555` vs `api/routes.py:102-104` | `/status` is documented as engine/version/RAM/parser/privacy; implementation returns `schemaVersion` + `state` | FR-SYS-02 cannot be satisfied; UI uses fixtures | Implement contract or narrow the doc |
| D-06 | `FR-SYS-01` vs `design.md:172,325` | LOCAL chip vs LOCAL APP | Low user impact; spec inconsistency | Design copy deck wins under the stated precedence; update FR-SYS-01 text |
| D-07 | `docs/licensing.md` vs `ingest/native/pymupdf_native.py` | Note says no code imports it yet; code imports it | Stale licensing record; decision appears uninformed | Update note; obtain owner decision |
| D-08 | `FR-ING-01`, `NFR-CAP-01` vs `ingest/job.py` and web client | Soft 50-page limit with override to 100; implementation has `MANY_PAGES = 100000` and no UI override | A 51-page upload is rejected with no usable override; an API caller can bypass the intended ceiling | Set override to 100; add UI or remove the hint |
| D-09 | `NFR-TEST-04` vs `e2e/parity/parity.spec.ts` | Requirement says landmark geometry within tolerance; test says it does not enforce comparison | M0 acceptance is overstated | Implement the comparison or mark NFR-TEST-04 not met |
| D-10 | `design.md` defect list no seed data in production vs `HomeLive.tsx` | Live Home uses fixture user/team/role and fixture status | Demo identity appears in the real product | Bind real settings or hide fields |
| D-11 | `docs/system-architecture.md` section 11 vs `api/routes.py` | RFC 7807 problem details with `code` + `hint`; implementation raises plain `detail` strings | Client cannot rely on one error shape | Normalize error responses |
| D-12 | `docs/dependencies.md:8` vs `apps/server/pyproject.toml:17` | Manifest versions are floors; `rapidfuzz==3.14.1` is an exact pin | Policy drift and harder upgrades | Use floor or document the exception |
| D-13 | `docs/system-architecture.md:504-505` vs `api/jobs.py` | Jobs are persisted and marked `interrupted`/resumable; runner is in-memory only | NFR-REL-04 is not implemented | Implement persistence or defer explicitly |
| D-14 | `PROGRESS.md:35` vs current test run | 46 pytest at M1 vs 132 now | Stale, but not false at the time | Update PROGRESS with current counts |
| D-15 | `AGENT_PROMPT.md` section 5 vs repository | README, CI, and notices listed as required | Release/onboarding incomplete | M7 or earlier |
| D-16 | `docs/licensing.md` status vs code state | Note says implementation starts only after the note exists; note is untracked and stale | Decision has no reviewed record | Commit decision record before further PyMuPDF work |

---

## 6. Traceability matrix for audit scope

This is a targeted matrix, not a replacement for a full requirements traceability file. Verified means a test or runtime check in this audit directly exercises it.

### 6.1 Functional requirements

| Requirement | Implementation evidence | Verification | Status |
|---|---|---|---|
| FR-HOME-01 profile/counts | `HomeLive` uses fixture greeting; no server settings/counts | None for live identity/counts | **Partially implemented** |
| FR-HOME-02 upload PDF | Hidden file input + button; no drag/drop | Live e2e not run; API ingest tested | **Partially implemented** |
| FR-HOME-03 sample PDF | No live control; fixture PDF exists | None | **Not implemented** |
| FR-HOME-04 templates grid/count/filter/search | Live tile lists max 3; no count/filter; search input is inert | None | **Partially implemented** |
| FR-ING-01 validate upload | Magic/size at API; page/encryption/corruption in worker | `test_ingest.py`, `test_api_ingest.py` | **Partially implemented** (page override/UI gap) |
| FR-ING-02 sandbox | Subprocess with wall-clock/memory/output caps | Wall-clock/cancel tests; memory cap untested | **Partially verified** |
| FR-ING-03 job/SSE/cancel | Job runner, SSE, cancel endpoint, analysis progress | Echo/SSE/cancel tests; no running-ingest cancel test; no UI cancel | **Partially implemented** |
| FR-ING-04 extraction coverage | PyMuPDF extractor behind port | 99% character coverage test; boundary test | **Implemented and verified** |
| FR-ING-05 role accuracy | Heuristics + fixture assertions | Fixture role assertions; no 85% labelled metric | **Partially verified** |
| FR-ING-07 columns | Flow node with columns/gap/rule | `test_newsletter_two_column_flow` | **Implemented and verified** |
| FR-ING-08 slots/shared furniture | `slots.py`, shared header/footer/title | Shared footer/pagenum/slot tests | **Implemented and verified** |
| FR-ING-10 constraints | Measured constraints + violations | Original passes, +30% violates | **Implemented and verified** |
| FR-ING-11 fonts/review | Font resolver + review items | Helvetica alias review test | **Implemented and verified** |
| FR-ING-12 confidence/review | Node/template confidence + review queue | Confidence range/review id tests | **Implemented and verified** (banner is M4) |
| FR-ING-13 validators | Contrast/clipped/overlap/imageDpi; no table validator | Four scans tested | **Partially implemented** |
| FR-ING-14 fidelity | Not implemented (M3) | None | **Not implemented** |
| FR-SYS-01 top nav/badge | TopBar with LOCAL APP chip; Home/Templates/Documents/Models/Privacy | E2E a11y routes pass | **Implemented** (doc text conflict) |
| FR-SYS-02 computed status | Live screens use fixture/hard-coded values; `/status` partial | None | **Partially implemented** |
| FR-SYS-05 error boundary/hints | ErrorBoundary exists; fetch errors show raw detail | No failure-path e2e | **Partially implemented** |
| FR-SYS-07 list pages | `/templates`, `/documents` routes absent | Top nav links 404 | **Not implemented** |
| FR-TPL-01 analysis header/proceed | Live analysis header; Proceed always enabled; no export | Live e2e not run | **Partially implemented** |
| FR-TPL-02 review queue/accept all | Issues tab only; no accept-all transaction | None | **Not implemented** |
| FR-MODE-01 mode picker | Fixture-gated static screen | No live template path | **Planned/static only** |
| FR-MAN-01 manual editor | Fixture-only editor | None | **Planned/static only** |
| FR-AI-01 AI Assist | Fixture-only chat/diff UI | None | **Planned/static only** |
| FR-RUL-01 rule kinds | `packages/rules` placeholder | None | **Not implemented** |
| FR-EXP-01 export PDF | No export job | None | **Not implemented** |
| FR-SET-01 settings shell | Fixture-only settings | None | **Planned/static only** |

### 6.2 Non-functional requirements

| Requirement | Evidence | Status |
|---|---|---|
| NFR-A11Y-01 no serious/critical axe | 8 routes pass | **Implemented and verified** |
| NFR-SEC-02 DNS rebinding/CSRF/Host checks | Security matrix and app tests pass | **Implemented and verified** |
| NFR-SEC-03 redaction/write-only keys | Redaction + vault tests pass | **Implemented and verified** |
| NFR-REL-01 kill-9 WAL recovery | Crash test passes | **Implemented and verified** |
| NFR-REL-03 migration + backup | Migration tests pass | **Implemented and verified** |
| NFR-REL-04 interrupted job recovery | No persistence/marking/resume | **Not implemented** |
| NFR-TEST-03 fixture corpus | 7 PDFs, no Devanagari/scanned/missing-font fixture | **Partially implemented** |
| NFR-TEST-04 landmark parity | Artifact capture only, no tolerance assertion | **Partially implemented** |
| NFR-TEST-05 op apply/invert property | Hypothesis test passes | **Implemented and verified** (except invalid-op API path) |
| NFR-MAINT-03 coverage floor | No coverage run | **Not measured** |
| NFR-MAINT-04 schema freshness | Generator not run; dirty generated files | **Unverified** |
| NFR-MAINT-05 import boundaries | PyMuPDF boundary test passes; placeholder TS packages | **Partially verified** |
| NFR-PERF-03 2-page/20-page timing | 2-page <=10s test passes; 20-page not tested | **Partially verified** |
| NFR-CAP-01 2000 nodes/page, 50/100 pages | No node cap; page override mismatch | **Partially implemented** |
| NFR-LIC-01 LICENSE/About/README/notices | LICENSE present; three other artifacts absent | **Partially implemented** |
| NFR-OBS-02 diagnostics bundle | Not implemented | **Not implemented** |
| NFR-SEC-08 dependency audit | No CI/audit run | **Unverified** |
| NFR-PRIV-04 copy lint | ESLint copy-lint active and passing | **Implemented and verified** |
| NFR-FID-07 no literal metrics | ESLint no-literal-metrics active and passing | **Implemented and verified** |

## 7. Software testing life cycle and SQA assessment

### 7.1 STLC phases

| Phase | Evidence | Assessment |
|---|---|---|
| Requirements analysis | Detailed FR/NFR set, D-007/OQ-1, spec precedence order | Strong specification depth; no testability review record and no requirement-to-test matrix |
| Test planning | No test plan document; Makefile and scripts define commands | Commands are clear, but entry/exit criteria, environments, and ownership are implicit |
| Test design | Pytest suites, axe routes, parity capture, no-network test, Hypothesis ops test | Good backend design; frontend and acceptance design thin |
| Environment setup | `uv`, Node, pnpm, SQLite, Playwright configs | Reproducible locally; no CI environment or pinned toolchain record |
| Execution | 132 pytest, 15 Vitest, 15 Playwright passed locally | Real evidence, but not continuous and not recorded as an artifact |
| Closure | `PROGRESS.md` claims; no milestone report found | Closure evidence is insufficient |

### 7.2 SQA strengths

- Security is treated as an architectural concern, not an afterthought: loopback-only defaults, Host/Origin/token checks, SameSite session cookie, no CORS, write-only secret vault, redaction tests, and a security-header middleware.
- The backend uses ports/adapters at the extraction and provider boundaries. PyMuPDF is isolated behind `native/pymupdf_native.py`, and provider calls are behind a `FakeProvider` seam.
- The domain model is validated with Pydantic; the op log has apply/invert property testing, which is a strong pattern for manual editing and undo/redo.
- The fixture corpus is generated and deterministic, with a manifest. Encrypted, malformed, image-only, 2-column, orientation, and 6-page cases exist.
- Accessibility is tested across eight routes, including a not-found route and the dev UI, not only the happy path.
- A no-network test exists to protect the local-only promise.
- Copy linting and a no-literal-metrics rule encode product constraints in tooling rather than prose.

### 7.3 SQA gaps

| Gap | Consequence | Recommended control |
|---|---|---|
| No CI | Regressions are found only when someone runs scripts locally; no durable green history | Add GitHub Actions or equivalent with the same commands |
| No requirement traceability file | Cannot prove coverage or detect orphan tests | Add `docs/requirements-traceability.md` with requirement -> test -> evidence |
| No test plan | Entry/exit criteria and environments are undocumented | One-page plan per milestone |
| No defect tracker/export | The 500 defect and other findings are not tracked with severity/owner/status | Use issues or a checked-in defect log |
| No code review evidence | Security and data-model changes have no second reader | Require PR review before each milestone commit |
| No frontend component tests | Most UI logic is untested; fixture/live regressions are easy | Add Vitest + React Testing Library for screens/hooks/stores |
| No live e2e in this run | The actual claim of M2 cannot be verified end to end | Run live suite after port conflict is resolved |
| No performance/chaos suite | NFR-PERF and NFR-REL claims are partly unproven | Add 20-page timing, kill-9 during job, interrupted-job tests |
| No dependency/security audit | NFR-SEC-08 is unverified | Add `pnpm audit`/`pip-audit`/OSV scan in CI |
| No coverage measurement | NFR-MAINT-03 has no number | Add coverage run with a floor |
| No visual acceptance | NFR-TEST-04 is not enforced | Compare landmark geometry and record owner sign-off |
| No memory-cap test | Sandbox memory protection is only inspected | Add a child process that exceeds the cap and assert failure mode |
| No orphan-blob test | Failed uploads may accumulate data | Assert cleanup or document retention |

### 7.4 Test-quality observations

- The suite is fast and mostly deterministic. The 32-second backend run is practical for local iteration and CI.
- Several tests assert fixture-specific values. That is acceptable for M2 fixture acceptance, but it does not prove general extraction accuracy.
- Role accuracy has fixture assertions but no labelled 85% metric. FR-ING-05 should not be marked fully verified.
- The parity suite is intentionally a capture harness. Its filename and comments are clear, but a reader could mistake passing tests for tolerance acceptance. The report should continue to call this out.
- The live suite exists and is well targeted, but it could not start because a server occupied port 8000. A passing fixture suite does not compensate for a missing live suite.

---

## 8. Quality gate results

### 8.1 Commands run in this audit

| Gate | Command | Result | Notes |
|---|---|---|---|
| Backend tests | `uv run pytest -q` | **132 passed in 32.23s** | Includes committed M1 and uncommitted M2 suites |
| Frontend unit | `npx vitest run` | **2 files, 15 tests passed in 2.05s** | Both files in `packages/ui` |
| Fixture e2e | `npx playwright test` | **15 passed in 19.5s** | Fixture config only |
| Lint | `npx eslint .` | **0 errors, 2 warnings** | Warnings in `AnalysisLive.tsx:123:5` and `:183:9` |
| Python lint | `uv run ruff check .` | Pass | No findings |
| Python types | `uv run pyright` | Pass | No findings |
| TS types | 5 project checks (`tsc --noEmit`) | Pass all | app, ui, doc-schema, render-core, rules |
| Schema freshness | Generator + `git status` check | **Not run** | Would regenerate tracked files; generated JSON already modified |
| Full gate | `make check` | **Not run** | Make unavailable; `check.ps1` would mutate tracked schemas |
| Live e2e | `npx playwright test -c playwright.live.config.ts` | **Blocked** | Port 8000 in use by PID 22444 |

### 8.2 Gate interpretation

- Local green is meaningful but not a release gate. There is no CI attestation, no coverage artifact, and no signed test report.
- The fixture e2e suite passes on a fixture-only config. It exercises accessibility, no-network behavior, and screenshots, not live ingestion.
- The schema-freshness gate is currently **red by construction**: `packages/doc-schema/schema/openapi.json` and `schema.json` are modified in the working tree. Even if their content matches the generator, the script compares `git status`, so it will fail until the files are intentionally regenerated and committed or reverted.
- The two ESLint warnings are not release blockers, but one unused disable comment and one exhaustive-deps warning should be cleaned before calling the gate clean.
- The live e2e failure is environmental, not a code failure. It remains an evidence gap because M2 acceptance depends on live behavior.

### 8.3 Commands not run and why

| Command | Reason |
|---|---|
| `make check` | `make` unavailable; underlying `check.ps1` mutates tracked schema files |
| Schema generator | Would write tracked files, violating read-only audit constraint |
| `uv sync` | Could change the environment and lockfile; not needed for audit |
| Live e2e after killing server | Would require terminating a pre-existing process without owner permission |
| Coverage run | Not part of current scripts; would add artifacts without a defined floor |
| Dependency audit | No configured tool; should be added, not improvised |

---

## 9. Estimation methodology and missing inputs

### 9.1 What the repository proves

- Five commits on one day, ordered as spec -> restructure -> M0 -> M1 -> M2 groundwork.
- A large dirty tree that includes most of M2.
- Test counts and command durations from this audit.
- No time logs, no issue estimates, no sprint records, no review timestamps, no CI durations, no team roster, and no cost data.

### 9.2 What it does not prove

- Elapsed engineering hours.
- Number of engineers or reviewers.
- Cost, velocity, or productivity.
- Whether work was continuous or batched.
- Whether M0/M1/M2 were approved at the claimed times.

Commit timestamps are especially weak evidence here because all commits are from one day and the M2 work is uncommitted. A 1h47m gap between M1 and M2 commits cannot be converted into effort.

### 9.3 Recommended estimation method

1. **Reconstruct actuals from primary records.** Collect owner time logs, issue tracker timestamps, CI run durations, review timestamps, and milestone approval messages. Do not infer from Git alone.
2. **Normalize scope per milestone.** Count implemented endpoints, screens, tests, and requirements delivered, not files touched. Separate committed from uncommitted work.
3. **Use reference classes.** Compare similar local-first document tools at the same milestone, or use prior projects with recorded actuals. State the reference class and its limits.
4. **Use three-point estimates for remaining work.** For each milestone, record optimistic, most likely, and pessimistic values with assumptions. Report a range, never a single false-precise number.
5. **Expose uncertainty.** Mark estimates low confidence until actuals exist. Re-estimate after each gate.
6. **Separate effort from calendar time.** Availability, review latency, and CI queue time are different variables.
7. **Do not price licensing or legal work into engineering estimates.** Treat those as owner/legal decisions with their own inputs.

### 9.4 Missing inputs required before any numeric estimate

| Input | Why needed | Current state |
|---|---|---|
| Owner/team availability | Converts effort to calendar time | Unknown |
| Time logs or issue timestamps | Actual effort per milestone | Absent |
| Milestone acceptance records | Defines done and rework | Absent/ambiguous |
| CI run history | Build/test feedback time | Absent |
| Defect history | Rework rate | Absent |
| Reference-class data | Calibration | Absent |
| Remaining scope approved | Prevents estimating unapproved work | M3-M7 only planned |
| Licensing/distribution decision | Can change architecture and scope | Provisional |

**Audit position:** no numeric estimate is defensible from this repository. Any hours, rates, or dates in a downstream report would be invented and should be rejected.

---

## 10. Licensing, third-party, and owner decisions

### 10.1 Current state

| Item | State | Evidence |
|---|---|---|
| Project licence | AGPL-3.0-or-later declared | `package.json`; `LICENSE` contains AGPL-3.0 text |
| PyMuPDF decision | Provisional | `docs/decisions.md` D-007/OQ-1 |
| PyMuPDF usage | Imported by native extractor | `ingest/native/pymupdf_native.py` |
| Licensing note | Present but untracked and stale | `docs/licensing.md` says no code imports PyMuPDF yet |
| Third-party notices | Absent | `THIRD_PARTY_NOTICES.md` missing |
| About dialog | Absent | No About component found |
| README | Absent | Root and server README missing |
| Dependency inventory | Partial | Manifests exist; no generated notices or audit |
| `rapidfuzz` | Exact pin `==3.14.1` | `apps/server/pyproject.toml` |

### 10.2 Why this matters

`docs/licensing.md` itself states that the obligations include keeping `LICENSE`, adding a `THIRD_PARTY_NOTICES.md`, showing licence information in About, and not shipping without the owner decision. The implementation has now crossed the line the note drew: it imports PyMuPDF while the note still describes a future integration. That makes the record inaccurate and weakens the claim that the decision was made before use.

The audit does not provide legal advice and does not assert that AGPL or a commercial PyMuPDF licence is required. It does assert that the repository currently lacks the artefacts needed to support whatever distribution model the owner chooses.

### 10.3 Owner decisions required

| Decision | Options | Consequence |
|---|---|---|
| PyMuPDF licensing | Accept AGPL obligations; buy a commercial licence; replace the extractor | Affects distribution, source-offer obligations, and possibly the extractor architecture |
| Distribution model | Private/internal only; public binary; SaaS; source distribution | Determines which obligations and notices apply |
| Project licence | Keep AGPL-3.0-or-later; change | Must be consistent across manifests, LICENSE, README, About |
| Third-party notice scope | Runtime deps only; dev deps; fonts; model weights | Determines notice content and review burden |
| Font licensing | Bundle only redistributable fonts; document aliases | Missing-font fixtures and font review depend on it |
| Contributor terms | DCO/CLA or none | Needed before outside contributions |
| Telemetry stance | None; local-only diagnostics | Must match Privacy screen and no-network test |

### 10.4 Licensing acceptance criteria

- D-007/OQ-1 is resolved and recorded as Accepted, with the chosen PyMuPDF path.
- `docs/licensing.md` is updated to reflect actual imports and is committed.
- `LICENSE` remains present and matches the declared licence.
- `THIRD_PARTY_NOTICES.md` exists and covers runtime dependencies and fonts.
- README states the licence and local-only posture.
- About shows the project licence and third-party notice location.
- Dependency audit/notice generation is part of CI.
- No release artifact is produced until the owner signs off on the distribution model.

## 11. Risks and blockers

### 11.1 Severity model

| Severity | Meaning |
|---|---|
| P0 | Immediate release/security/data-loss blocker; stop and fix now |
| P1 | Blocks a milestone or release gate; fix before approval |
| P2 | Significant correctness/coverage/operability gap; schedule before release |
| P3 | Quality/polish/policy drift; fix when touching the area |

**No confirmed P0 was found.** This is a local-only application with loopback defaults, origin/token checks, and no evidence of remote exposure. P0 could emerge if the app is distributed without resolving licensing, or if the server is bound beyond loopback without a new threat review.

### 11.2 Risk register

| ID | Risk | Severity | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R-01 | M2 continues without approval, making status and rollback ambiguous | P1 | High (already happening) | High | Freeze, commit or stash deliberately, write M2 report, obtain approval | Owner |
| R-02 | PyMuPDF/AGPL distribution obligation is discovered late | P1 now; P0 if distributed | Medium | High | Resolve D-007 before release; add notices/About/README | Owner |
| R-03 | Live UI displays fixture identity/status as if real | P1 | High | High (trust/privacy perception) | Bind live settings/status or hide fields; add live e2e assertions | Frontend |
| R-04 | Invalid owned op crashes request with 500 | P1 | Medium | Medium (client sees server fault; logs noisy) | Validate before invert; catch `ValidationError` -> 422 | Backend |
| R-05 | No CI means regressions reach the owner unnoticed | P1 | High | High | Add CI with lint/type/test/schema/live-smoke jobs | Maintainer |
| R-06 | Visual parity is not actually enforced | P1 | High | Medium (acceptance false positive) | Implement landmark comparison and owner sign-off | Frontend/owner |
| R-07 | Live Analysis dead-ends at Mode | P1 | High | High (core flow unusable) | Make Mode accept live template ids or remove CTA until M4 | Frontend |
| R-08 | Frontend regressions are not caught by tests | P1 | High | Medium | Add screen/hook tests and one live happy-path e2e | Frontend |
| R-09 | Page limit is inconsistent and override unreachable | P2 | Medium | Medium | Set override to 100; add UI; test 51/101 pages | Backend/UI |
| R-10 | SSE early failure leaves a stuck analysis screen | P2 | Medium | Medium | Treat non-terminal errors as failure; add timeout/retry UI | Frontend |
| R-11 | Job/event lists grow without bound | P2 | Medium (long sessions) | Medium (memory) | Bound/prune completed jobs; persist for recovery | Backend |
| R-12 | Failed/cancelled ingestion leaves orphan blobs | P2 | Medium | Medium (disk/privacy) | Delete on terminal failure or add retention job | Backend |
| R-13 | Sandbox memory cap is untested and has a documented race | P2 | Low/Medium | High if hostile input | Add memory-exhaustion test; document residual risk | Backend/security |
| R-14 | Error shapes differ across endpoints | P2 | High | Medium (client complexity) | Central exception handlers with `code`/`hint` | Backend |
| R-15 | No requirement traceability | P2 | High | Medium (audit/coverage) | Add matrix and update per milestone | Maintainer |
| R-16 | Missing fixtures for Devanagari/scanned/missing-font | P2 | Medium | Medium (untested real cases) | Add fixtures with licences and expected outcomes | Backend |
| R-17 | No dependency/security audit | P2 | Medium | Medium | Add CI audit job | Maintainer |
| R-18 | `rapidfuzz` exact pin contradicts policy | P3 | High | Low | Use floor or document exception | Backend |
| R-19 | Stray `tsconfig.tsbuildinfo` is untracked | P3 | High | Low | Ignore/remove generated artifact | Frontend |
| R-20 | README/onboarding missing | P3 now; P1 before handoff | High | Medium | Write README with setup/run/test/security notes | Maintainer |

### 11.3 Active blockers

| Blocker | Detail | Workaround |
|---|---|---|
| Live e2e port conflict | `http://127.0.0.1:8000/api/v1/status` is already used; PID 22444 is a pre-existing `python.exe -m templix.serve`, parent 25452 | Obtain owner permission to stop it, or run with a dedicated port/reuseExistingServer after confirming which process is authoritative |
| Schema freshness | Generated `openapi.json`/`schema.json` are already modified; gate compares `git status` | Regenerate intentionally, review diff, and commit/revert; do not run blindly |
| Full `make check` | `make` unavailable; `check.ps1` mutates tracked files | Run read-only gates individually, as this audit did; use CI for the full gate |
| Licensing decision | D-007/OQ-1 provisional while PyMuPDF is imported | Owner decision before any distribution |

---

## 12. Prioritised recommendations

### P0

None confirmed for local-only use. If the product will be distributed, treat the unresolved PyMuPDF licence as P0 and stop release until D-007 is resolved.

### P1 - before M2 approval or any release

| # | Recommendation | Why | Acceptance evidence |
|---|---|---|---|
| 1 | Freeze M2 scope and record actual status in `PROGRESS.md` | Removes gate ambiguity | PROGRESS entry with commit/working-tree hash and status labels |
| 2 | Obtain owner go-ahead for M2 and resolve D-007/OQ-1 | Restores the documented process and licensing basis | Signed decision + updated `docs/licensing.md` |
| 3 | Commit the M2 work in reviewable slices or explicitly park it | Makes the baseline reproducible | Clean tree or documented patch series |
| 4 | Add CI for lint, types, unit, schema freshness, and fixture e2e | Prevents local-only assurance | Green CI run linked in PROGRESS |
| 5 | Run the live e2e suite and record results | M2 acceptance requires live proof | Live run log with 2 tests passing or defects filed |
| 6 | Fix the op-log 500: validate before invert or catch `ValidationError` | Client should receive 422, not a server fault | Regression test for `set_slot` non-object and double `clear_slot` |
| 7 | Replace fixture identity/status on live screens | Prevents false product state | Live e2e asserts settings/status values, not Sarah Lin |
| 8 | Make Mode usable for live templates or hide the CTA | Removes core-flow dead end | Live path reaches a meaningful next step |
| 9 | Implement NFR-TEST-04 landmark comparison | Converts parity from capture to acceptance | Test fails when geometry exceeds tolerance; owner sign-off recorded |
| 10 | Add `README.md` and `THIRD_PARTY_NOTICES.md`; add About licence text | Required by project and licensing rules | Files present; About shows licence/notice |
| 11 | Add frontend tests for live Home/Analysis/upload/error paths | Current UI logic has no automated coverage | Vitest + RTL suite; at least one live happy path |

### P2 - before release

| # | Recommendation | Why |
|---|---|---|
| 12 | Add cancel control and robust SSE failure handling | FR-ING-03 and stuck-screen risk |
| 13 | Align page-limit override to 100 and expose it in the UI, or remove the hint | Spec/implementation mismatch |
| 14 | Bound/prune job and event lists; add interrupted-job handling | NFR-REL-04 and memory growth |
| 15 | Add orphan-blob cleanup/retention | Disk/privacy hygiene |
| 16 | Normalize error responses to `code` + `hint` | Documented API contract |
| 17 | Add memory-cap and running-cancel tests | Sandbox claim needs proof |
| 18 | Add missing fixture categories (Devanagari, scanned, missing font) | NFR-TEST-03 |
| 19 | Add dependency/security audit and coverage measurement | NFR-SEC-08, NFR-MAINT-03 |
| 20 | Add a requirements traceability matrix | Auditability and coverage |
| 21 | Add irregular-table validator or explicitly defer it | FR-ING-13 coverage |
| 22 | Add 20-page performance test | NFR-PERF-03 partial |

### P3 - quality/polish

| # | Recommendation |
|---|---|
| 23 | Clean the two ESLint warnings |
| 24 | Remove/ignore `tsconfig.tsbuildinfo` |
| 25 | Reconcile `LOCAL` vs `LOCAL APP` in FR-SYS-01 |
| 26 | Fix D-032/D-034 references and move D-032 out of Proposed |
| 27 | Use a floor for `rapidfuzz` or document the pin |
| 28 | Fix `layerCount` for nested groups |
| 29 | Update `PROGRESS.md` test counts and current milestone |

---

## 13. Next-step sequence respecting owner gates

1. **Record and freeze.** Update `PROGRESS.md` to state the true baseline: M1 awaiting approval, M2 uncommitted work present, live e2e blocked, schema gate red. Do not start M3.
2. **Resolve the live-run environment.** Confirm whether PID 22444 is the intended server. With owner permission, stop it or run the live suite against a dedicated port. Capture the live result. Do not kill an unfamiliar process silently.
3. **Close M1 evidence.** Run the schema generator intentionally, review the diff, and commit or revert it. Run the full gate in an environment where `make check` is meaningful. Attach the result to the M1 closure record.
4. **Obtain the licensing decision.** Resolve D-007/OQ-1; update `docs/licensing.md`; add `THIRD_PARTY_NOTICES.md`, README licence text, and About text. This is an owner decision, not an engineering inference.
5. **Fix P1 defects.** At minimum: op-log 500, live fixture identity/status, Mode dead end, parity enforcement, and CI. Add regression tests for each.
6. **Prepare the M2 acceptance package.** Include the M2 report, test evidence (132 pytest, 15 fixture e2e, live e2e), known gaps, and a commit/patch reference.
7. **Obtain M2 approval.** Only after approval should M3 renderer/fidelity work start. Do not let unapproved M2 scope blend into M3.

If the owner chooses to defer M2, the working tree should be parked deliberately and `PROGRESS.md` should say so. Leaving it dirty while claiming M1-complete is the current ambiguity.

---

## 14. Evidence index and audit limitations

### 14.1 Evidence index

| Area | Evidence |
|---|---|
| Git | `git status --porcelain`, `git log`, `git diff --stat`, per-commit stats, branch/tag checks |
| Milestones | `PLAN.md`, `PROGRESS.md`, `AGENT_PROMPT.md` |
| Requirements | `docs/functional-requirements.md`, `docs/non-functional-requirements.md` |
| Architecture | `docs/system-architecture.md`, `docs/decisions.md` |
| Design/copy | `docs/design.md`, `apps/web/src/lib/copy.ts`, `packages/ui/src/components/TopBar.tsx` |
| Licensing | `docs/licensing.md`, `LICENSE`, manifests, `docs/dependencies.md` |
| Server core | `apps/server/templix/api/{app,routes,security,jobs,logging}.py` |
| Data model | `apps/server/templix/model/{schema,patch}.py`, `store/db.py` |
| Ingest | `apps/server/templix/ingest/*`, `ingest/native/{pymupdf_native.py,__main__.py}` |
| Entry points | `apps/server/templix/serve.py`, `apps/web/vite.config.ts` |
| Frontend live | `apps/web/src/App.tsx`, `lib/api.ts`, `screens/{HomeLive,AnalysisLive,Home,AppShell,ModePicker,ManualEditor,AiAssist,Settings}.tsx` |
| Tests | `apps/server/tests/*`, `packages/ui/tests/*`, `e2e/*`, `e2e/parity/*`, `e2e/live/*` |
| Gates | `Makefile`, `scripts/check.ps1`, `package.json`, `apps/server/pyproject.toml`, `vitest.config.ts` |
| Fixtures | `fixtures/generated/` (7 PDFs + `manifest.json`) |
| Commands | `uv run pytest -q`; `npx vitest run`; `npx playwright test`; `npx eslint .`; `uv run ruff check .`; `uv run pyright`; 5x `tsc --noEmit` |
| Reproduction | Inline `TestClient` script for invalid owned op -> 500 |

### 14.2 Verification limits

- No live e2e run. The live suite was written but blocked by the port conflict.
- No schema-generator run. The freshness gate was not executed because it mutates tracked files.
- No full `make check`. The equivalent read-only gates were run individually.
- No coverage measurement, dependency audit, performance test, chaos test, or memory-cap test.
- No manual visual review of every screen at every breakpoint. Accessibility was automated via axe.
- No legal review. Licensing statements are risk flags, not legal conclusions.
- No numeric effort estimate. The repository lacks the primary records needed to support one.
- The audit did not terminate PID 22444 or modify source, specs, configuration, generated schemas, or commits. The only created file is this report.

### 14.3 Bottom line

Templix has real engineering substance and a strong specification base. Its current problem is not lack of code; it is **lack of a trustworthy gate**. The M2 work is unapproved and uncommitted, the live path is partly fixture-backed, one malformed request returns 500, the parity requirement is not enforced, and the licensing decision is stale while PyMuPDF is already imported.

The next responsible action is to stop adding scope, make the baseline honest in `PROGRESS.md`, resolve the live-run and licensing blockers, fix the P1 defects, and then seek M2 approval with evidence. M3 should not start before that gate is real.
