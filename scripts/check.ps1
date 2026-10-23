# Templix check gate: lint + typecheck + unit + a11y-contrast. Makefile delegates here (single source of truth).
# Native tools (uv) write progress to stderr; we gate on explicit exit codes instead of ErrorActionPreference.
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot | Split-Path
Push-Location $root
$failed = 0

# 1. eslint: code rules + copy-lint (NFR-PRIV-04) + no-literal-metrics (NFR-FID-07) + no-innerHTML etc.
Write-Host "[check] lint (eslint: code + copy-lint + no-literal-metrics)" -ForegroundColor Cyan
npx eslint . --no-warn-ignored
if ($LASTEXITCODE -ne 0) { $failed = 1 }

# 2. typecheck all TS workspaces
Write-Host "[check] typecheck" -ForegroundColor Cyan
npx tsc --noEmit -p packages/ui
if ($LASTEXITCODE -ne 0) { $failed = 1 }
npx tsc --noEmit -p apps/web
if ($LASTEXITCODE -ne 0) { $failed = 1 }
npx tsc --noEmit -p packages/render-core
if ($LASTEXITCODE -ne 0) { $failed = 1 }
npx tsc --noEmit -p packages/rules
if ($LASTEXITCODE -ne 0) { $failed = 1 }
npx tsc --noEmit -p packages/doc-schema
if ($LASTEXITCODE -ne 0) { $failed = 1 }

# 3. python lint + types (uv-managed, apps/server)
Write-Host "[check] python: ruff + pyright" -ForegroundColor Cyan
Push-Location (Join-Path $root "apps\server")
uv sync --extra dev
if ($LASTEXITCODE -ne 0) { $failed = 1 }
uv run ruff check .
if ($LASTEXITCODE -ne 0) { $failed = 1 }
uv run pyright .
if ($LASTEXITCODE -ne 0) { $failed = 1 }
Pop-Location

# 4. unit tests (vitest; pytest when python tests exist)
Write-Host "[check] unit tests" -ForegroundColor Cyan
npx vitest run
if ($LASTEXITCODE -ne 0) { $failed = 1 }
Write-Host "[check] fixtures (generate for Python tests)" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "fixtures.ps1")
if ($LASTEXITCODE -ne 0) { $failed = 1 }
Push-Location (Join-Path $root "apps\server")
if (Test-Path "tests") {
  uv run pytest -q
  if ($LASTEXITCODE -ne 0) { $failed = 1 }
} else {
  Write-Host "  [pytest] no tests, skipping" -ForegroundColor Gray
}
Pop-Location

# 5. schema freshness: generated doc-schema must equal committed output (D-015)
Write-Host "[check] schema freshness (regenerate + diff)" -ForegroundColor Cyan
Push-Location (Join-Path $root "apps\server")
uv run python -m templix.model.generate
if ($LASTEXITCODE -ne 0) { $failed = 1 }
Pop-Location
$stale = git status --porcelain -- packages/doc-schema/src/index.ts packages/doc-schema/schema
if ($stale) {
  $failed = 1
  Write-Host "  [schema] doc-schema is stale - run 'uv run python -m templix.model.generate' in apps/server and commit" -ForegroundColor Red
  Write-Host $stale
}

Pop-Location
if ($failed) { Write-Host "[check] FAILED" -ForegroundColor Red; exit 1 }
Write-Host "[check] OK" -ForegroundColor Green
