# Dev servers: FastAPI backend (127.0.0.1:8000) + Vite web (5173, proxies /api). Add ?fixtures=1 to
# the browser URL for demo fixtures; the server prints the one-time session URL on startup.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot | Split-Path
$server = Start-Process -PassThru -NoNewWindow -FilePath "uv" `
  -ArgumentList "run", "python", "-m", "templix.serve" `
  -WorkingDirectory (Join-Path $root "apps\server")
try {
  Push-Location (Join-Path $root "apps\web")
  pnpm dev
} finally {
  Pop-Location
  if (!$server.HasExited) { Stop-Process -Id $server.Id -Force }
}
