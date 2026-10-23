# Templix

Templix turns a reference PDF into a reusable document template, then produces new documents from
that template. It is **local-first**: the FastAPI server binds to `127.0.0.1`, data lives in SQLite
and a local blob store, and there is no telemetry, CDN, or cloud dependency at runtime.

## Status

- **M0 (foundation/design system)** and **M1 (backend core, data model, security)** are implemented.
- **M2 (ingestion, live Home/Analysis)** is committed on `main` but **not approved**.
- A narrow **manual text-edit/export slice** is committed on top of M2; it is not M3.
- **M3 (renderer, rules, export, fidelity)** has not started.

`PROGRESS.md` is the authoritative status record; `docs/audits/engineering-baseline-audit-v2.md`
lists the open P1 evidence gaps. Do not treat committed M2 code as acceptance.

## Requirements

- Node.js 22+ and pnpm 10 (via corepack)
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- PowerShell (Windows PowerShell 5.1+ or `pwsh` 7+) for the scripts, or run the underlying commands directly
- Playwright Chromium (installed by `setup`)

## Setup

```powershell
pnpm setup
```

This installs workspace packages, the Playwright Chromium build, and the Python environment.

## Develop

```powershell
pnpm dev
```

Starts the API on `http://127.0.0.1:8000` and Vite on `http://localhost:5173` (Vite proxies
`/api`). The server prints a one-time session URL; open it so the page can exchange the launch
token for the `SameSite=Strict` session cookie. Add `?fixtures=1` to any URL to render the demo
dataset instead of the live API.

## Gates

```powershell
pnpm check   # eslint, 5x tsc, vitest, ruff, pyright, pytest, schema freshness
pnpm e2e     # fixture Playwright suite, then the live suite (starts its own servers)
```

CI runs the same commands in `.github/workflows/ci.yml`; the schema-freshness step regenerates
`packages/doc-schema` and fails if the committed output differs.

## Repository layout

| Path | Contents |
|---|---|
| `apps/web` | React SPA, live API client, screens |
| `apps/server` | FastAPI server, SQLite store, ingestion pipeline |
| `packages/ui` | Design-system components and theme tokens |
| `packages/doc-schema` | Generated JSON Schema, OpenAPI, TypeScript types |
| `packages/render-core`, `packages/rules` | M3 placeholders |
| `e2e` | Playwright fixture and live suites |
| `fixtures` | Deterministic synthetic PDFs (generated, never real data) |
| `docs` | Requirements, architecture, decisions, licensing, audits |

## Security and privacy

The local API enforces a Host/Origin allowlist, a per-launch session token, and security headers
on every response. Provider keys are write-only and stored outside SQLite (keyring, with an
encrypted fallback). There is no CORS and no outbound network call unless a provider is configured.

Report security issues privately to the repository owner; do not open a public issue with details.

## Licence

Templix is licensed under **AGPL-3.0-or-later** (see `LICENSE`). PyMuPDF is dual-licensed
AGPL-3.0/commercial; using it under AGPL is provisional pending the owner decision D-007/OQ-1 in
`docs/licensing.md`. Third-party components and fonts are listed in `THIRD_PARTY_NOTICES.md`.
No release should be distributed until that decision is recorded.
