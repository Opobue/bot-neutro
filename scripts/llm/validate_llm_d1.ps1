param(
  [Parameter(Mandatory = $true)][string]$RepoRoot,
  [Parameter(Mandatory = $true)][string]$SubmissionSlug,   # ej: gemini_d1_2026-01-09
  [Parameter(Mandatory = $true)][string]$LlmOutputPath,    # txt/md con el output del LLM
  [switch]$KeepSubmission                                  # si no, se borra al final
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
  throw $Message
}

function RunExternal([string]$Label, [scriptblock]$Script) {
  Write-Host "==> $Label"
  $out = & $Script 2>&1
  $out | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Fail "Fallo en '$Label' (exit $LASTEXITCODE)"
  }
}

function RunExternalCapture([string]$Label, [scriptblock]$Script) {
  Write-Host "==> $Label"
  $out = & $Script 2>&1
  $out | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Fail "Fallo en '$Label' (exit $LASTEXITCODE)"
  }
  return ($out -join "`n")
}

# 1) Ir a repo y sincronizar
Set-Location $RepoRoot

git status | Out-Host

# Bloqueo si hay cambios sin commitear
$porcelain = (git status --porcelain)
if ($porcelain) {
  Fail "WORKTREE NO LIMPIO: commitea o stash antes de validar. (git status --porcelain no vacío)"
}

RunExternal "git fetch" { git fetch origin }
RunExternal "git switch" { git switch develop }
RunExternal "git pull" { git pull --ff-only }

# 2) Paths canónicos (según Pack Mode)
$repomixDir      = Join-Path $RepoRoot "docs\llm\repomix"
$evidenceDir     = Join-Path $RepoRoot "docs\llm\evidence"
$submissionsDir  = Join-Path $RepoRoot "docs\llm\submissions"

New-Item -ItemType Directory -Force -Path $repomixDir, $evidenceDir, $submissionsDir | Out-Null

# 3) Generar repomix-head y repomix-output (local)
$sha = (git rev-parse HEAD).Trim()

$headPath = Join-Path $repomixDir "repomix-head.txt"
Set-Content -Path $headPath -Value $sha -NoNewline -Encoding ascii

# Limpia outputs previos
Remove-Item (Join-Path $repomixDir "repomix-output*.xml") -ErrorAction SilentlyContinue

# Repomix (evitar recursión ignorando repomix/evidence locales)
RunExternal "repomix" {
  npx --yes repomix --style xml --parsable-style --include-full-directory-structure `
    --include "docs/**,src/**,tests/**,scripts/**,.github/**,pyproject.toml,.gitignore,README*,LICENSE*" `
    --ignore  "**/node_modules/**,**/.venv/**,**/.git/**,**/dist/**,**/build/**,**/.tmp_bench/**,**/__pycache__/**,**/.mypy_cache/**,**/.ruff_cache/**,**/.pytest_cache/**,**/docs/llm/repomix/**,**/docs/llm/evidence/**" `
    --split-output 20mb `
    -o (Join-Path $repomixDir "repomix-output.xml")
}

# Verificaciones mínimas de integridad
$repomixFiles = Get-ChildItem -Path $repomixDir -Filter "repomix-output*.xml"
if (-not $repomixFiles) { Fail "Repomix no generó repomix-output*.xml en $repomixDir" }

Select-String -Path $repomixFiles.FullName -Pattern ".github/workflows" -Quiet | % { if (-not $_) { Fail "FALTA .github/workflows en RepoPack" } }
Select-String -Path $repomixFiles.FullName -Pattern "pyproject.toml"   -Quiet | % { if (-not $_) { Fail "FALTA pyproject.toml en RepoPack" } }
Select-String -Path $repomixFiles.FullName -Pattern ".gitignore"       -Quiet | % { if (-not $_) { Fail "FALTA .gitignore en RepoPack" } }

# 4) EvidencePack (derivado) — pasar lista real de XMLs (no glob string)
$repomixXmls = @($repomixFiles | Select-Object -ExpandProperty FullName)

$rawEvidence = RunExternalCapture "build evidence pack" {
  python "scripts\llm\build_evidence_pack.py" `
    --repomix $repomixXmls `
    --head $headPath `
    --out $evidenceDir
}
$lines = $rawEvidence -split "(`r`n|`n|`r)" | Where-Object { $_.Trim() -ne "" }
$jsonLines = $lines | Where-Object { $_.Trim() -match "\.json$" }
if (-not $jsonLines) { Fail "build_evidence_pack.py no devolvió ruta .json. Salida: $rawEvidence" }
$evidencePath = $jsonLines[-1].Trim()

if (-not $evidencePath) { Fail "build_evidence_pack.py no devolvió ruta" }
if (-not ($evidencePath -match "\.json$")) { Fail "EvidencePath no parece JSON: $evidencePath" }
if (-not (Test-Path $evidencePath)) { Fail "EvidencePack no existe en disco: $evidencePath" }
Write-Host "EvidencePack => $evidencePath"

# 5) Crear submission desde output del LLM
if (-not (Test-Path $LlmOutputPath)) { Fail "LlmOutputPath no existe: $LlmOutputPath" }

$submissionPath = Join-Path $submissionsDir ($SubmissionSlug + ".md")
$llmText = Get-Content -Path $LlmOutputPath -Raw -Encoding utf8
Set-Content -Path $submissionPath -Value $llmText -Encoding utf8
Write-Host "Submission => $submissionPath"

# 6) Lint (propaga exit code)
RunExternal "lint D1 output" {
  python "scripts\llm\lint_d1_output.py" $submissionPath --evidence $evidencePath
}
Write-Host "LINT OK ✅"
Write-Host "PASS ✅"

# 7) Limpieza opcional
if (-not $KeepSubmission) {
  Remove-Item $submissionPath -Force
  Write-Host "Submission removida (KeepSubmission=false)"
}
