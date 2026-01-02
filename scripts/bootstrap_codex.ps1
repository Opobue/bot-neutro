$ErrorActionPreference = "Stop"

$repoRoot = Get-Location
$pyprojectPath = Join-Path $repoRoot "pyproject.toml"

if (-not (Test-Path $pyprojectPath)) {
    throw "Ejecuta este script desde la raíz del repo (pyproject.toml no encontrado)."
}

$venvPath = ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

if (-not (Test-Path $activateScript)) {
    throw "No se encontró el script de activación: $activateScript"
}

& $activateScript

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

pytest -q
pytest --cov=src --cov-fail-under=80
ruff check .
mypy src/
