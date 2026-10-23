# Generate synthetic fixture PDFs into fixtures/generated/ (reportlab; dev-only).
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot | Split-Path
Push-Location (Join-Path $root "apps\server")
try {
  uv run python (Join-Path $root "fixtures\generate.py")
  $code = $LASTEXITCODE
} finally {
  Pop-Location
}
exit $code
