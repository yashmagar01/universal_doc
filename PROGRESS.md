# Progress

## Status: M1 complete, awaiting owner approval (2026-10-18)

M0 shipped (`fef0efd`). M1 (backend core, data model, security) is built with all gates green. Stopped per
AGENT_PROMPT §4.2 — M2 does not start without Yash's go-ahead.

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

### Gates

- `scripts/check.ps1`: eslint (code + copy-lint + no-literal-metrics), typecheck (5 tsconfigs), ruff +
  pyright strict, 15 vitest, 46 pytest, schema freshness — all green in the final M1 run.
- `apps/server`: `uv run ruff check .` → 0; `uv run pyright .` → 0; `uv run pytest -q` → 46 passed.

### Open / unverified

- Landmark/pixel parity numeric comparison vs Stitch (from M0) — pending visual sign-off.
- `httpx2` (dev) was added for starlette's `TestClient`; confirm it as test tooling (M1 report Q).

### Next

M2 (ingestion) after Yash's go-ahead on the M1 report.
