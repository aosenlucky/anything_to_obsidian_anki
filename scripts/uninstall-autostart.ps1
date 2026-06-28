$ErrorActionPreference = "Stop"

$taskName = "KnowledgeTreeHollowService"
$startupPath = Join-Path ([Environment]::GetFolderPath("Startup")) "$taskName.cmd"
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
  Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
  Write-Host "Removed scheduled task: $taskName"
} else {
  Write-Host "Scheduled task not found: $taskName"
}

if (Test-Path -LiteralPath $startupPath) {
  Remove-Item -LiteralPath $startupPath -Force
  Write-Host "Removed Startup fallback: $startupPath"
}
