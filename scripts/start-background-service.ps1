$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$port = 8000
$python = Join-Path $root ".venv\Scripts\python.exe"
$statusPath = Join-Path $root "app\storage\service_status.json"

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

$status = @{
  service = "KnowledgeTreeHollowService"
  port = $port
  url = "http://127.0.0.1:$port"
  started_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}
$status | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statusPath -Encoding UTF8

Write-Host "Knowledge Tree Hollow service is available at http://127.0.0.1:$port"
