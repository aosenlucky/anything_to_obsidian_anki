param(
  [Parameter(Mandatory=$true)][string]$CloudInboxUrl,
  [Parameter(Mandatory=$true)][string]$AgentToken,
  [Parameter(Mandatory=$true)][string]$VaultPath
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "config.yaml"
$envPath = Join-Path $root ".env"

if (-not (Test-Path -LiteralPath $configPath)) {
  Copy-Item -LiteralPath (Join-Path $root "config.yaml.example") -Destination $configPath
}

if (-not (Test-Path -LiteralPath $envPath)) {
  Copy-Item -LiteralPath (Join-Path $root ".env.example") -Destination $envPath
}

$config = Get-Content -LiteralPath $configPath -Raw
$config = $config -replace 'vault_path:\s*"[^"]*"', ('vault_path: "' + ($VaultPath -replace '\\','/') + '"')
$config = $config -replace 'enabled:\s*false', 'enabled: true'
$config = $config -replace 'api_url:\s*"[^"]*"', ('api_url: "' + $CloudInboxUrl.TrimEnd('/') + '"')
Set-Content -LiteralPath $configPath -Value $config -Encoding UTF8

$envContent = Get-Content -LiteralPath $envPath -Raw
if ($envContent -match 'CLOUD_INBOX_AGENT_TOKEN=') {
  $envContent = $envContent -replace 'CLOUD_INBOX_AGENT_TOKEN=.*', ('CLOUD_INBOX_AGENT_TOKEN=' + $AgentToken)
} else {
  $envContent = $envContent.TrimEnd() + "`r`nCLOUD_INBOX_AGENT_TOKEN=$AgentToken`r`n"
}
Set-Content -LiteralPath $envPath -Value $envContent -Encoding UTF8

Write-Host "Local config.yaml and .env updated."
