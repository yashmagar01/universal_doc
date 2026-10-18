# Templix — Build Plan

Status: M0 approved (2026-10-18). This file records the plan and the owner's conditions.

## Approved plan

Milestones M0–M7 as per `AGENT_PROMPT.md` §6, one milestone per owner go-ahead. Current milestone: **M0**.

- M0 Foundation & design system (six screens, ui package, fixtures, lints)
- M1 Backend core, data model, security
- M2 Ingestion (native pass + heuristics)
- M3 render-core, rules, export, fidelity
- M4 Template review & editing
- M5 Manual Edit
- M6 Providers, Settings, AI Assist
- M7 Hardening & release

## Owner conditions (2026-10-18)

1. **Milestone gates preserved.** M1 never starts until M0 is complete, `make check` is green,
   `PROGRESS.md` is updated, and the milestone report (AGENT_PROMPT §8) is delivered with evidence.
2. **OQ-1 / AGPL-3.0 provisionally approved.** Before PyMuPDF implementation (M2), write a licensing
   note (`docs/licensing.md`) covering distribution model and commercial-use considerations; record the
   decision and unresolved concerns transparently.
3. **Restructure approved.** Six spec files → `docs/`; `stitch_templix_document_recreation_studio/` →
   `design/stitch/`; keep `AGENT_PROMPT.md` at root. Verify cross-references after moving; inspect git
   state first; do not delete source material.
4. **Windows-first.** PowerShell supported; Makefile stays the canonical task interface; fallback
   scripts invoke the **same underlying checks** (Makefile recipes call the ps1 scripts — one source of
   truth). Prerequisites documented in README.
5. **M0 safeguards.** Screens are typed React implementations using `design.md` as spec; screenshots
   are not visually inspectable in this environment — record visually unverified areas in the M0 report;
   no pixel-parity claims. Verify current stable dependencies, licences, compatibility, lockfile
   reproducibility; no unnecessary dependencies for the gallery (`/dev/ui` route, no Storybook).
6. **Quality gates non-negotiable.** Never lower thresholds; report failures with evidence, root-cause,
   remediation. Distinguish implemented / tested / partially verified / unverified work.
7. **Git workflow.** Inspect git state before changes (repo was **not** a git repo initially — history
   starts fresh at M0 bootstrap). Meaningful conventional commits at natural boundaries, tests with
   code. No push/publish without explicit approval.
8. **Defaults** from `docs/decisions.md` open questions: AGPL-3.0 (provisional), synthetic fixtures +
   `fixtures/private/` untracked, Windows first, Devanagari = Should/P2, PDF-only v1, adapter order
   OpenAI-compatible → Anthropic → Google, source files ignored in v1.

## Environment facts

- Windows 11, PowerShell; Node 22.22.3, pnpm 10.18.0, Python 3.13.14 (floor ≥ 3.12), uv 0.7.20, git 2.49.
- `make` is **not installed** — Makefile targets delegate to `scripts/*.ps1` so both interfaces stay green.
- Spec deviations are Proposed ADRs `D-031+` recorded in `docs/decisions.md`; tooling-forced choices are
  documented in the milestone report.

## M0 task breakdown

1. Bootstrap: git init, `.gitignore`, restructure docs/ + design/stitch/, LICENSE (AGPL-3.0),
   .editorconfig, .nvmrc, .python-version, PLAN.md/PROGRESS.md.
2. Monorepo: pnpm workspaces (`apps/web`, `packages/{doc-schema,render-core,rules,ui}`), uv project
   (`apps/server`), Makefile + scripts/check.ps1, CI workflow skeleton.
3. Dependencies (verify current stable at install, licence allow-list per dependencies.md §7).
4. Tailwind v4 theme (`packages/ui/src/theme.css` per design.md §2.4), self-hosted Inter + Material
   Symbols; no runtime CDN (defect §12-15).
5. `packages/ui`: components of design.md §4 + `/dev/ui` gallery route covering all states.
6. Six screens as typed React routes (design.md §8) with fixture data behind a dev flag, corrections
   from design.md §12 applied.
7. Quality lints: copy-lint (NFR-PRIV-04) + no-literal-metrics (NFR-FID-07); token contrast test
   (NFR-A11Y-03).
8. `make fixtures`: ≥ 4 synthetic PDFs (single-column, two-column newsletter w/ image+rule+box,
   image-heavy, vector-heavy) via reportlab (dev dep).
9. e2e: Playwright + axe smoke on all routes; landmark-parity scaffolding (`e2e/parity/regions.ts`);
   no-network Playwright request assertion.
10. `make check`, `PROGRESS.md`, milestone report → stop for approval.

## Risks

- Fidelity ≥ 0.97 gate (M3) is the hardest target; per-page heatmap diagnosis planned.
- AGPL compliance for distribution (M2 licensing note).
- Windows CI matrix; Chromium determinism.
- Perf budgets (NFR-PERF-02) require disciplined re-render scoping.

## Visual verification caveat (condition 5)

The coding agent cannot view `screen.png` files in this environment. Visual truth = `design.md §8` +
`design.md §12` corrections + `code.html` structure. stitch parity is verified by the landmark-geometry
e2e tests (NFR-TEST-04) and side-by-side artifacts listed in design.md §14; a human (Yash) reviews the
parity PNGs. Unverified areas are listed in the M0 report.
