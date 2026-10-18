# Templix setup: pnpm install + playwright chromium + uv sync. Idempotent.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot | Split-Path

Write-Host "[setup] pnpm install" -ForegroundColor Cyan
Push-Location $root
corepack enable 2>$null | Out-Null
pnpm install | Out-Host
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[setup] playwright chromium" -ForegroundColor Cyan
npx playwright install chromium | Out-Host
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[setup] uv sync (apps/server)" -ForegroundColor Cyan
Push-Location (Join-Path $root "apps\server")
try {
  python -m uv sync 2>$null | Out-Host
  if ($LASTEXITCODE -ne 0) { uv sync --all-extras | Out-Host }
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }

Pop-Location
Write-Host "[setup] done" -ForegroundColor Green
