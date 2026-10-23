# Third-party notices

Templix is distributed under AGPL-3.0-or-later (see `LICENSE`). This file lists the third-party
components shipped with the application, their licences, and the notices those licences require.
Dev/build-only tooling is listed separately; it is not part of a runtime distribution.

Versions are pinned in `pnpm-lock.yaml` and `apps/server/uv.lock`; the licences below apply to
those pinned versions. If a dependency is added or upgraded, update this file in the same change.
This is an engineering inventory, not legal advice.

## Runtime — web

| Component | Licence | Copyright / notice |
|---|---|---|
| React, React DOM | MIT | Copyright Meta Platforms, Inc. and affiliates |
| React Router | MIT | Copyright Remix Software, Inc. |
| Inter (variable font, `@fontsource-variable/inter`) | SIL Open Font License 1.1 | Copyright The Inter Project Authors |
| Material Symbols Outlined (`material-symbols`) | Apache-2.0 | Copyright Google LLC |

Web packages bundle their transitive dependencies; those retain their upstream licences (MIT,
ISC, BSD, or Apache-2.0 as declared in each package). No font is fetched from a CDN at runtime.

## Runtime — server

| Component | Licence | Copyright / notice |
|---|---|---|
| FastAPI | MIT | Copyright Sebastián Ramírez |
| Uvicorn | BSD-3-Clause | Copyright Encode OSS Ltd. |
| Pydantic, pydantic-core | MIT | Copyright Pydantic Services Inc. and contributors |
| SQLAlchemy | MIT | Copyright Michael Bayer and contributors |
| Alembic | MIT | Copyright Michael Bayer and contributors |
| keyring | MIT | Copyright Jason R. Coombs and contributors |
| python-multipart | Apache-2.0 | Copyright Andrew Dunham and contributors |
| rapidfuzz | MIT | Copyright Max Bachmann and contributors |
| **PyMuPDF** | **AGPL-3.0 or commercial** | Copyright Artifex Software, Inc. |

### PyMuPDF notice

Templix uses PyMuPDF through the isolated adapter in `apps/server/templix/ingest/native/`.
PyMuPDF is dual-licensed: AGPL-3.0 (the option currently assumed) or a commercial licence from
Artifex Software. Under AGPL-3.0, distributing Templix requires providing the complete
corresponding source under AGPL-3.0 and preserving this notice. The decision is **provisional**
(D-007/OQ-1 in `docs/decisions.md`, `docs/licensing.md`) and must be confirmed by the owner before
any distribution. Replacing the adapter with a permissively licensed extractor is the documented
fallback.

The Python runtime also pulls transitive packages (Starlette, AnyIO, Mako, greenlet, typing
extensions, and platform-specific Uvicorn extras). Their licences are declared in `uv.lock` and
remain in force.

## Development and build tooling

Vite, TypeScript, Tailwind CSS, ESLint, Prettier, Vitest, Testing Library, happy-dom, Playwright,
Ruff, Pyright, pytest, Hypothesis, and reportlab are used to build and test Templix only. They are
not distributed as part of the application. Playwright's Chromium build is test tooling; export
features must not assume a system browser is present.

## Fonts

Only self-hosted, redistributable fonts may be bundled. Inter is OFL-1.1; Material Symbols is
Apache-2.0. The missing-font behaviour and font substitution rules are documented in
`docs/decisions.md` (D-018). Do not add a font without recording its licence here.
