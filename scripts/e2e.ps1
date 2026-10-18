# Playwright e2e (functional + parity artifacts + no-network assertion).
# Native tools write progress to stderr; gate on exit code instead of ErrorActionPreference.
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot | Split-Path
Push-Location (Join-Path $root "e2e")
npx playwright test
exit $LASTEXITCODE
