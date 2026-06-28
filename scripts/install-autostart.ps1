$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$taskName = "KnowledgeTreeHollowService"
$scriptPath = Join-Path $PSScriptRoot "start-background-service.ps1"
$startupPath = Join-Path ([Environment]::GetFolderPath("Startup")) "$taskName.cmd"

if (-not (Test-Path -LiteralPath $scriptPath)) {
  throw "start-background-service.ps1 not found."
}

$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
  -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn
$userId = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -MultipleInstances IgnoreNew

$installedBy = "scheduled task"
try {
  Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Start local Knowledge Tree Hollow automation service at Windows logon." `
    -ErrorAction Stop `
    -Force | Out-Null
} catch {
  $installedBy = "Startup folder fallback"
  $cmd = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`"`r`n"
  Set-Content -LiteralPath $startupPath -Value $cmd -Encoding ASCII
  Write-Warning "Scheduled Task install failed: $($_.Exception.Message)"
}

& $scriptPath

Write-Host "Installed autostart via ${installedBy}: $taskName"
if (Test-Path -LiteralPath $startupPath) {
  Write-Host "Startup fallback: $startupPath"
}
Write-Host "Open http://127.0.0.1:8000 to view the console."
