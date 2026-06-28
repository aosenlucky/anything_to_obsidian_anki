$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$url = "http://127.0.0.1:8000"
$starter = Join-Path $PSScriptRoot "start-background-service.ps1"

& $starter

Start-Process $url
