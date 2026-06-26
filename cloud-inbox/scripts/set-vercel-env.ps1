param(
  [Parameter(Mandatory=$true)][string]$SupabaseUrl,
  [Parameter(Mandatory=$true)][string]$SupabaseServiceRoleKey,
  [Parameter(Mandatory=$true)][string]$InboxToken,
  [Parameter(Mandatory=$true)][string]$AgentToken,
  [string]$Environment = "production",
  [string]$VercelToken = ""
)

$ErrorActionPreference = "Stop"

function Set-VercelEnv {
  param(
    [string]$Name,
    [string]$Value
  )
  $temp = New-TemporaryFile
  try {
    Set-Content -LiteralPath $temp -Value $Value -NoNewline
    if ($VercelToken) {
      Get-Content -LiteralPath $temp | npx vercel env add $Name $Environment --token $VercelToken
    } else {
      Get-Content -LiteralPath $temp | npx vercel env add $Name $Environment
    }
  } finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
  }
}

Set-VercelEnv "SUPABASE_URL" $SupabaseUrl
Set-VercelEnv "SUPABASE_SERVICE_ROLE_KEY" $SupabaseServiceRoleKey
Set-VercelEnv "INBOX_TOKEN" $InboxToken
Set-VercelEnv "AGENT_TOKEN" $AgentToken

Write-Host "Vercel environment variables submitted for $Environment."
