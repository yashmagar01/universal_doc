# Playwright e2e: fixture-mode suite (functional + parity artifacts + no-network) then the live
# suite (real FastAPI server + Vite without VITE_FIXTURES). Fixtures are regenerated for uploads.
# Native tools write progress to stderr; gate on exit code instead of ErrorActionPreference.
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot | Split-Path
& (Join-Path $PSScriptRoot "fixtures.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Push-Location (Join-Path $root "e2e")
# Dedicated port: a dev server or another app may already own 5173.
$env:E2E_WEB_PORT = "5175"
npx playwright test
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
npx playwright test -c playwright.live.config.ts
$code = $LASTEXITCODE
Pop-Location
exit $code
