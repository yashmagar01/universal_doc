# Progress

## Status: M0 complete, awaiting owner approval (2026-10-18)

Milestone gates for M0 are green. M1 is **not** started. Stopped per PLAN.md §1 / AGENT_PROMPT §8.

### M0 — Foundation & design system

- **Landed:** pnpm workspace (`apps/web` + `packages/ui`), Vite + React 19 + TS + Tailwind v4, five-token
  design system (`packages/ui`), six screens (home, mode, analysis, manual, ai-assist, settings) + dev gallery
  + 404, fixture backend (`VITE_FIXTURES=1`, `apps/web/src/fixtures/`) with 4 fixture PDFs, copy-lint +
  no-literal-metrics ESLint rules.
- **Gates (all green):**
  - `scripts/check.ps1` → lint (eslint + copy-lint + no-literal-metrics), typecheck, ruff + pyright, unit
    (15 vitest: token-contrast + counter). Exit 0.
  - `scripts/e2e.ps1` → 15 Playwright tests: axe no serious/critical on 8 routes (NFR-A11Y-01), zero-network
    assertion, parity artifact capture. Exit 0. Stable across 3 consecutive runs.
- **Parity (NFR-TEST-04):** scaffolded. `e2e/parity/regions.ts` lists our data-qa landmark regions per screen;
  `e2e/parity/parity.spec.ts` renders each screen at 1333×900 @ DPR 1.2 and writes screenshot + bbox JSON to
  `artifacts/parity/` for visual review. The numeric stitch↔ours ±4% comparison is **deferred** — the Stitch
  exports carry no data-qa, use an external-CDN layout, and the region mapping needs visual sign-off against
  the PNGs (agent cannot view PNGs). See M0 report.

### Open / unverified

- Landmark parity numeric comparison vs Stitch (see above) — pending visual mapping sign-off.
- Pixel fidelity against `screen.png` — unverified (no visual inspection in this environment).

### Next

M1 (functional requirements) after Yash's go-ahead on the M0 report.
