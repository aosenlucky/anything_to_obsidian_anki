param(
  [string]$VercelToken = ""
)

$ErrorActionPreference = "Stop"
npm install
npm run build

if ($VercelToken) {
  npx vercel --prod --yes --token $VercelToken
} else {
  npx vercel --prod --yes
}
