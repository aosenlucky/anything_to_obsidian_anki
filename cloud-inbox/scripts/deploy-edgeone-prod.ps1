param(
  [Parameter(Mandatory=$true)][string]$EdgeOneApiToken,
  [string]$ProjectName = "anything_to_obsidian_anki",
  [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

npm install
npm run build
npx edgeone@latest makers deploy -n $ProjectName -t $EdgeOneApiToken -e $Environment
