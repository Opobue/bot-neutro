Param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$SubmissionPath,
  [switch]$Bridge
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) {
  $repoRoot = (Get-Location).Path
}

$bridgeScript = Join-Path $repoRoot "scripts/llm/bridge_d1.py"
$lintScript = Join-Path $repoRoot "scripts/llm/lint_d1_output.py"
$evidenceDir = Join-Path $repoRoot "docs/llm/evidence"
$evidenceFile = Get-ChildItem $evidenceDir -Recurse -Filter "*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $evidenceFile) {
  throw "No se encontró EvidencePack en $evidenceDir"
}

if ($Bridge) {
  $bridgedPath = "$SubmissionPath.bridge.md"
  python $bridgeScript $SubmissionPath --root $repoRoot --out $bridgedPath
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  python $lintScript $bridgedPath --evidence $evidenceFile.FullName
  exit $LASTEXITCODE
} else {
  python $lintScript $SubmissionPath --evidence $evidenceFile.FullName
  exit $LASTEXITCODE
}
