# Templix — Non-Functional Requirements

Version 0.1 · Companion docs: `functional-requirements.md`, `system-architecture.md`, `decisions.md`.

**How to read.** Every NFR has a measurable target and a verification method. `Gate` = a CI or release check
that must pass. Unless stated, targets apply on the **reference machine**: 4-core x86-64 CPU (~2020 laptop
class), 8 GB RAM, SSD, **no GPU**, Windows 11 / macOS 13+ / Ubuntu 22.04, Chrome/Edge/Firefox current stable.

---

## 1. Performance (`NFR-PERF`)

| ID | Requirement | Target | Verification | Gate |
|---|---|---|---|---|
| NFR-PERF-01 | Cold start of server + SPA ready | ≤ 5 s to interactive Home | e2e timing on reference machine | Release |
| NFR-PERF-02 | Keystroke → preview update (Manual mode), 2-page letter document | p95 ≤ 100 ms, p50 ≤ 50 ms | Playwright perf trace over 200 keystrokes | CI |
| NFR-PERF-03 | Native ingestion (no VLM) of a 2-page, ≈ 24-layer PDF | ≤ 10 s to *template ready* incl. fidelity score; ≤ 45 s for 20 pages | Fixture timing | CI (2 p) / Release (20 p) |
| NFR-PERF-04 | PDF export of a 2-page document | ≤ 5 s end-to-end; Chromium warm start ≤ 1.5 s | Export benchmark | CI |
| NFR-PERF-05 | Canvas interaction on analysis screen (drag/resize layer, ≈ 500 nodes/page) | ≥ 55 fps; p95 frame ≤ 20 ms | Performance trace | Release |
| NFR-PERF-06 | Memory | Server ≤ 600 MB RSS idle→peak for a 20-page ingest; SPA ≤ 400 MB | Process sampling | Release |
| NFR-PERF-07 | Autosave round trip | p95 ≤ 150 ms; never blocks typing | Trace | CI |
| NFR-PERF-08 | First meaningful paint of a template card grid with 100 templates | ≤ 1.5 s; virtualised list for > 200 items | Synthetic data | Release |

## 2. Fidelity and correctness (`NFR-FID`)

| ID | Requirement | Target | Verification | Gate |
|---|---|---|---|---|
| NFR-FID-01 | Round-trip (template + original content → export) vs reference | Overall score ≥ **0.97** on the *digital-native* fixture set; ≥ 0.93 on every fixture | `fidelity.py` over fixtures; per-page JSON artifacts | CI (fixtures in `fixtures/`) |
| NFR-FID-02 | Text exactness | 100 % of extractable characters preserved in order (Unicode NFC) after round-trip | Text diff | CI |
| NFR-FID-03 | Locked-layer integrity | After any sequence of Content edits or accepted AI proposals, all template nodes' geometry/style hashes are unchanged | Property-based test (hypothesis/fast-check) | CI |
| NFR-FID-04 | Determinism | Same inputs + same Chromium build → byte-identical page raster (± 0 px on fixtures) | Repeat-export test | CI |
| NFR-FID-05 | Export equals preview | Preview raster vs exported PDF raster SSIM ≥ 0.995 | Compare screenshots | CI |
| NFR-FID-06 | Fonts | Zero silent substitutions: every non-exact font appears as a review item | Test with missing-font fixture | CI |
| NFR-FID-07 | Reported numbers are computed | No hard-coded quality/confidence/progress values in UI code | Lint rule (`no-literal-metrics`) + grep test + code review | CI |
| NFR-FID-08 | Parser accuracy tracking | Role accuracy, column detection, header/footer detection reported per fixture in CI summary | Report artifact | Report only |

## 3. Reliability and data integrity (`NFR-REL`)

| ID | Requirement | Target | Verification | Gate |
|---|---|---|---|---|
| NFR-REL-01 | No data loss on crash/kill | ≤ 1 s of edits lost; DB consistent after `kill -9` | Fault-injection test | CI |
| NFR-REL-02 | Atomic writes | Blob and DB writes via temp+rename / SQLite transactions | Code review + test | CI |
| NFR-REL-03 | Migrations | Forward-only, tested from every previous `schemaVersion`; automatic DB backup before migrating | Migration tests | CI |
| NFR-REL-04 | Job resilience | Server restart marks running jobs `interrupted`; resume or retry available | Test | CI |
| NFR-REL-05 | Graceful degradation | If Chromium/export unavailable: editing still works; if provider unreachable: Manual mode unaffected; clear error with remedy | Chaos tests | CI |
| NFR-REL-06 | Backup/restore | Template package + document export/import round-trips without loss | Test | Release |
| NFR-REL-07 | Provider calls | Timeouts (default 60 s, configurable), bounded retries with jitter on 429/5xx (max 2), never retry non-idempotent side effects | Unit tests with fake provider | CI |

## 4. Security (`NFR-SEC`)

| ID | Requirement | Target | Verification | Gate |
|---|---|---|---|---|
| NFR-SEC-01 | Network exposure | Server binds `127.0.0.1` only; refuses `0.0.0.0` unless explicitly configured with a warning | Test | CI |
| NFR-SEC-02 | Request authenticity | Every request needs the session token; `Host`/`Origin` allowlist; DNS-rebinding test passes | Security tests | CI |
| NFR-SEC-03 | Secrets | API keys only in OS keyring/encrypted vault; never in DB, logs, URLs, error bodies, exports, or the browser; redaction filter unit-tested against key-shaped strings for each provider | Tests + log scan | CI |
| NFR-SEC-04 | Untrusted files | PDFs parsed in a resource-limited subprocess (CPU time, memory, timeout); no embedded JS executed; decompression-bomb limits | Malformed/bomb fixtures | CI |
| NFR-SEC-05 | XSS/injection | No `innerHTML`/`dangerouslySetInnerHTML` with user or model text (lint rule); CSP `default-src 'self'`; link scheme allowlist | ESLint rule + e2e | CI |
| NFR-SEC-06 | SSRF controls on custom endpoint | Block link-local/metadata ranges; require HTTPS unless host is loopback/private with an explicit warning | Unit tests | CI |
| NFR-SEC-07 | AI write safety | Model output can only change allow-listed content paths; locked layers immutable (NFR-FID-03) | Adversarial prompt-injection test suite (≥ 25 cases) | CI |
| NFR-SEC-08 | Dependency hygiene | Lockfiles with hashes; `pip-audit` and `pnpm audit` have no unwaived high/critical findings; new deps require an ADR note in `dependencies.md` | CI jobs | CI |
| NFR-SEC-09 | Least privilege files | Data directory permissions `0700` (POSIX) / user-only ACL (Windows); uploads never executed or served from a path derived from filenames | Test | CI |
| NFR-SEC-10 | Secure defaults | No CORS wildcard; cookies HttpOnly + SameSite=Strict; security headers present | Header test | CI |

## 5. Privacy and transparency (`NFR-PRIV`)

| ID | Requirement | Target | Verification | Gate |
|---|---|---|---|---|
| NFR-PRIV-01 | No telemetry | Zero outbound requests except user-initiated provider calls and consented font downloads | Network-capture e2e test with provider disabled → 0 external requests | CI |
| NFR-PRIV-02 | Consent before egress | No document-derived bytes leave the machine before explicit consent for that provider/document | e2e with request interceptor | CI |
| NFR-PRIV-03 | Ledger completeness | 100 % of outbound provider requests have a ledger row (intent logged before send) | Test comparing interceptor vs DB | CI |
| NFR-PRIV-04 | Truthful copy | UI never claims "100 % on-device", "zero cloud" or legal compliance (FERPA/GDPR) | Copy lint (forbidden-phrases list) | CI |
| NFR-PRIV-05 | Data minimisation | AI authoring sends only the slot digest and user-provided material; page images only in opt-in VLM ingestion | Payload-shape tests | CI |
| NFR-PRIV-06 | Erasure | "Delete all data" removes DB, blobs, caches; template/document delete removes unreferenced blobs | Test | CI |
| NFR-PRIV-07 | Logs | Document text and prompts are not logged at default level; rotating logs ≤ 50 MB | Test | CI |

## 6. Cost efficiency (`NFR-COST`)

| ID | Requirement | Target | Verification | Gate |
|---|---|---|---|---|
| NFR-COST-01 | Single small edit ("shorten headline") | ≤ 3 k input tokens, ≤ 300 output tokens, 1 model call | Token accounting test with fake provider | CI |
| NFR-COST-02 | Typical full newsletter interview (≈ 7 sections) | ≤ 40 k total tokens | Scripted session | Report |
| NFR-COST-03 | Prompt caching friendliness | Stable prefix first; ≥ 60 % of input tokens identical across consecutive calls in a session | Prefix-diff test | CI |
| NFR-COST-04 | Cost visibility | Estimated spend shown per session and per provider; user-set soft budget with warning | UI test | Release |
| NFR-COST-05 | Zero-token operations | Manual mode, rules, fit, export, scoring consume no tokens | Test | CI |

## 7. Usability (`NFR-USA`)

| ID | Requirement | Target | Verification |
|---|---|---|---|
| NFR-USA-01 | Time to first recreated PDF for a new user with a sample | ≤ 5 minutes unaided | Usability session with 3 committee members |
| NFR-USA-02 | Clicks to change one headline from Home (existing doc) | ≤ 4 | Task test |
| NFR-USA-03 | Every error has a cause and a next step | 100 % of defined error codes have `hint` | Unit test over error registry |
| NFR-USA-04 | Terminology | Non-technical words ("layer", "template", "locked") consistent with `design.md §11` | Copy review |
| NFR-USA-05 | Undo | Every user-visible mutation is undoable | Property test over ops |
| NFR-USA-06 | State clarity | Every async action shows idle/loading/success/error | Component tests |

## 8. Accessibility (`NFR-A11Y`)

| ID | Requirement | Target | Verification | Gate |
|---|---|---|---|---|
| NFR-A11Y-01 | Standard | WCAG 2.2 AA for application chrome | axe-core in e2e on every route + manual keyboard/screen-reader pass (NVDA + VoiceOver) | CI + Release |
| NFR-A11Y-02 | Keyboard | All functionality operable without a mouse, including layer selection/nudging; visible 2-px focus ring using `primary` | e2e keyboard tests | CI |
| NFR-A11Y-03 | Contrast | Text ≥ 4.5:1, large text/UI ≥ 3:1 (tokens in `design.md` validated by script) | Token contrast test | CI |
| NFR-A11Y-04 | Semantics | Radix primitives for dialogs/tabs/accordions; ARIA labels on icon buttons; live regions for toasts, save state and counters (polite) | Review + axe | CI |
| NFR-A11Y-05 | Motion | `prefers-reduced-motion` disables non-essential transitions | Test | CI |
| NFR-A11Y-06 | Zoom/reflow | UI usable at 200 % browser zoom at 1280 px width | Manual | Release |
| NFR-A11Y-07 | Output accessibility | Exported PDF has document title and language metadata; tagged PDF is P3 | Inspect PDF | Release |

## 9. Compatibility and portability (`NFR-COMP`)

| ID | Requirement | Target |
|---|---|---|
| NFR-COMP-01 | OS | Windows 10/11, macOS 13+, Ubuntu 22.04+; paths and keyring behaviour tested on each in CI matrix (Windows first priority, OQ-3) |
| NFR-COMP-02 | Browsers | Latest two stable versions of Chrome, Edge, Firefox; Safari best-effort (not gated) |
| NFR-COMP-03 | Display | Min 1024 × 700; designed at 1600 px; high-DPI aware |
| NFR-COMP-04 | Offline | Everything except cloud AI calls and optional font download works with no network |
| NFR-COMP-05 | Runtime versions | Python ≥ 3.12, Node active LTS (≥ 22), Chromium via Playwright pinned in lockfile |
| NFR-COMP-06 | File compatibility | Reads PDF 1.4–2.0 (incl. object streams); exports PDF with embedded fonts viewable in Acrobat, Chrome, Preview |

## 10. Internationalisation (`NFR-I18N`)

| ID | Requirement | Target | Verification |
|---|---|---|---|
| NFR-I18N-01 | Unicode | UTF-8 everywhere; NFC normalisation on ingest; no truncation by byte length | Tests with emoji/ZWJ/combining marks |
| NFR-I18N-02 | Complex scripts | Devanagari (Marathi/Hindi) shaping correct in preview and export (FR-ING-18) | Fixture, visual diff |
| NFR-I18N-03 | UI language | English (en-IN default formats); strings externalised via a message catalogue so translation is possible later | Lint for hard-coded strings in components |
| NFR-I18N-04 | Dates/numbers | Locale-aware formatting using `Intl`; date slots store ISO-8601 and render by pattern | Tests |
| NFR-I18N-05 | RTL | Not in v1 (documented limitation) | — |

## 11. Maintainability and quality (`NFR-MAINT`)

| ID | Requirement | Target | Gate |
|---|---|---|---|
| NFR-MAINT-01 | Type safety | TS `strict` + `noUncheckedIndexedAccess`; Python typed with pyright strict (or mypy strict) on `templix/` | CI |
| NFR-MAINT-02 | Lint/format | ESLint + Prettier; Ruff (lint + format); zero warnings policy | CI |
| NFR-MAINT-03 | Test coverage | Unit coverage ≥ 80 % on `render-core`, `rules`, `ai/patches`, `ingest/fuse`; ≥ 60 % overall; coverage is a floor, not the goal | CI |
| NFR-MAINT-04 | Schema freshness | Generated types/JSON Schemas equal committed output | CI |
| NFR-MAINT-05 | Boundaries | Import-boundary lint: `render-core` and `rules` have no React/Node/DOM-global leaks beyond declared ones; PyMuPDF imported only inside `ingest/native` | CI |
| NFR-MAINT-06 | Documentation | Every public function in packages has TSDoc/docstring; ADRs updated with deviations | Review |
| NFR-MAINT-07 | Commit hygiene | Conventional commits; PR template with checklist (tests, docs, a11y, privacy copy) | Review |
| NFR-MAINT-08 | Module size | No source file > 500 lines without justification; functions ≤ 60 lines preferred | Review |

## 12. Testability (`NFR-TEST`)

| ID | Requirement | Target |
|---|---|---|
| NFR-TEST-01 | Test pyramid | Unit (vitest, pytest) → integration (API with fake provider) → e2e (Playwright) → visual regression (Stitch parity + fixtures) |
| NFR-TEST-02 | Fake provider | Deterministic fake LLM provider with scripted outputs and token accounting used for all AI tests; no network in CI |
| NFR-TEST-03 | Fixture corpus | ≥ 8 synthetic fixtures (single/multi-column, image heavy, vector heavy, Devanagari, missing font, scanned, malformed, encrypted) generated by script; real references live in `fixtures/private/` (git-ignored) |
| NFR-TEST-04 | Visual parity | Each of the six Stitch screens has a Playwright **landmark-geometry** test (named regions within ±8 CSS px / ±4 % size of the Stitch layout) plus side-by-side review artifacts; raw pixel diff is informational only because Stitch screenshots use different device-scale factors and demo data (`design.md §14`) |
| NFR-TEST-05 | Property tests | Patch application/inversion, locked-layer integrity, schema round-trip use property-based testing |

## 13. Observability (`NFR-OBS`)

| ID | Requirement | Target |
|---|---|---|
| NFR-OBS-01 | Structured JSON logs with request id, job id; levels configurable; secrets/text redacted |
| NFR-OBS-02 | `/status` and a downloadable **diagnostics bundle** (versions, config sans secrets, last errors, no document text) for support |
| NFR-OBS-03 | Job and AI timing (stage durations, latency, tokens) stored locally for the status UI |

## 14. Capacity and limits (`NFR-CAP`)

| ID | Limit |
|---|---|
| NFR-CAP-01 | Upload ≤ 50 MB; ≤ 50 pages (soft, overridable to 100); ≤ 2 000 nodes per page |
| NFR-CAP-02 | ≤ 500 templates / 2 000 documents per workspace without degraded UX (NFR-PERF-08) |
| NFR-CAP-03 | Op-log compaction: snapshot every 200 ops or 5 min; keep last 50 snapshots per document |
| NFR-CAP-04 | Single user, single machine; no concurrent multi-user writes |

## 15. Licensing and compliance (`NFR-LIC`)

| ID | Requirement |
|---|---|
| NFR-LIC-01 | The project licence (AGPL-3.0, D-007) is stated in `LICENSE`, About dialog, and README; third-party notices generated at build time |
| NFR-LIC-02 | Only dependencies with licences compatible with the project licence; bundled fonts must be OFL/Apache; user-uploaded fonts show a licence reminder |
| NFR-LIC-03 | No claim of regulatory compliance anywhere (see NFR-PRIV-04) |
