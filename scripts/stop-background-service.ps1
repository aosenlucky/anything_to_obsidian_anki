$ErrorActionPreference = "Stop"

$port = 8000
$connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
foreach ($connection in $connections) {
  if ($connection.OwningProcess) {
    Stop-Process -Id $connection.OwningProcess -Force
  }
}

Write-Host "Knowledge Tree Hollow service stopped if it was running."
