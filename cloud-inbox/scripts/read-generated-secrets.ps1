$ErrorActionPreference = "Stop"

$path = Join-Path (Split-Path -Parent $PSScriptRoot) "secrets.generated.env"
if (-not (Test-Path -LiteralPath $path)) {
  throw "secrets.generated.env not found. Generate it from the project root first."
}

Get-Content -LiteralPath $path
