$ErrorActionPreference = "Stop"

$ankiUrl = "http://127.0.0.1:8765"
$modelName = "Obsidian Basic"

$css = @'
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  max-width: 680px;
  margin: 0 auto;
  padding: 24px;
  color: #f4f7f5;
  background: #111715;
  line-height: 1.65;
}
.question,
.answer,
.lap-front,
.lap-answer {
  color: #f4f7f5;
}
.question,
.lap-front {
  font-size: 20px;
  font-weight: 650;
  line-height: 1.55;
}
.answer,
.lap-answer {
  font-size: 17px;
  line-height: 1.8;
}
.lap-answer p {
  margin: 0 0 0.8em;
}
hr#answer {
  border: none;
  border-top: 1px solid rgba(244, 247, 245, 0.22);
  margin: 20px 0;
}
.meta {
  margin-top: 18px;
  padding-top: 12px;
  border-top: 1px solid rgba(244, 247, 245, 0.14);
  color: #9da9a2;
  font-size: 12px;
  line-height: 1.55;
}
.source,
.section {
  display: inline-block;
  margin-right: 10px;
}
.front {
  text-align: center;
  padding-top: 40px;
}
.back {
  padding-top: 8px;
}
.card.nightMode,
.nightMode .card {
  color: #f4f7f5;
  background: #111715;
}
@media (prefers-color-scheme: light) {
  .card {
    color: #151a1d;
    background: #ffffff;
  }
  .question,
  .answer,
  .lap-front,
  .lap-answer {
    color: #151a1d;
  }
  hr#answer {
    border-top-color: rgba(21, 26, 29, 0.14);
  }
  .meta {
    border-top-color: rgba(21, 26, 29, 0.12);
    color: #69716d;
  }
}
'@

$templates = @{
  "Card 1" = @{
    Front = '<div class="card front"><div class="question">{{Front}}</div></div>'
    Back = '{{FrontSide}}<hr id="answer"><div class="card back"><div class="answer">{{Back}}</div><div class="meta">{{#Source}}<span class="source">来源：{{Source}}</span>{{/Source}}{{#Section}}<span class="section">{{Section}}</span>{{/Section}}</div></div>'
  }
}

function Invoke-Anki($action, $params) {
  $payload = @{ action = $action; version = 6; params = $params } | ConvertTo-Json -Depth 10
  $response = Invoke-WebRequest -UseBasicParsing -Uri $ankiUrl -Method Post -ContentType "application/json" -Body $payload
  $data = $response.Content | ConvertFrom-Json
  if ($data.error) {
    throw $data.error
  }
  $data.result
}

Invoke-Anki "updateModelStyling" @{ model = @{ name = $modelName; css = $css } } | Out-Null
Invoke-Anki "updateModelTemplates" @{ model = @{ name = $modelName; templates = $templates } } | Out-Null

Write-Host "Configured Anki model: $modelName"
