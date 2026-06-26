param(
  [Parameter(Mandatory=$true)][string]$CloudInboxUrl
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "config.yaml"

if (-not (Test-Path -LiteralPath $configPath)) {
  throw "config.yaml not found. Run scripts/configure-local-inbox.ps1 first."
}

$url = $CloudInboxUrl.TrimEnd("/")
$config = Get-Content -LiteralPath $configPath -Raw
$config = $config -replace 'api_url:\s*"[^"]*"', ('api_url: "' + $url + '"')
Set-Content -LiteralPath $configPath -Value $config -Encoding UTF8

Write-Host "cloud_inbox.api_url updated to $url"
