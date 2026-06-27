$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$port = 8000
$url = "http://127.0.0.1:$port"
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
  $python = "python"
}

$existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $existing) {
  Start-Process -FilePath $python `
    -ArgumentList "-m", "app.main", "serve", "--host", "127.0.0.1", "--port", "$port" `
    -WorkingDirectory $root `
    -WindowStyle Hidden
  Start-Sleep -Seconds 3
}

Start-Process $url
