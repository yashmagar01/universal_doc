# Dev server only (web). Server process arrives with M1.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot | Split-Path
Push-Location (Join-Path $root "apps\web")
pnpm dev
