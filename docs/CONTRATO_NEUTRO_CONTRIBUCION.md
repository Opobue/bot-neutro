# CONTRATO_NEUTRO_CONTRIBUCION

Documento de referencia oficial para cualquier persona (humana o IA) que abra un Pull Request en este repositorio.

## Checklist previo a abrir un PR
1. El PR cita explícitamente el/los contrato(s) habilitante(s) en su descripción.
2. `docs/HISTORIAL_PR.md` está actualizado si se tocaron contratos o el NORTE.
3. `pytest -q` y `pytest --cov=src --cov-fail-under=80` se ejecutaron (local o CI) y están en verde.
4. El PR tiene **una sola intención**; no mezcla temas.
5. La descripción del PR incluye TIPO (DESCUBRIR/DECIDIR/CAMBIAR/BLOQUEO) y referencia a secciones de contrato/ADR relevantes.

6. Verificación de realidad del NORTE:
   [ ] La orden/PR cita NORTE_VERSION_ACTUAL exactamente como aparece en `docs/02_ESTADO_Y_NORTE.md`.
   [ ] No se mencionan secciones o versiones de NORTE que no existan.

7. CI REAL vs futuro:
   [ ] Los checks de CI en la orden/PR corresponden a workflows existentes en `.github/workflows`, salvo que esta misma orden los cree o modifique.

8. Limpieza de artefactos IA:
   [ ] El texto no contiene patrones tipo "contentReference[", "oaicite:", "<<ImageDisplayed>>" salvo que sean ejemplos explícitos.

## Evidencia SKB (Repomix Pack) — Protocolo Manual

### CUÁNDO aplica (nivel estricto)
- Aplica SIEMPRE para cualquier PR.

### QUÉ artefactos se generan
- `repomix-head.txt` (SHA exacto).
- `repomix-output*.xml` (considerar split).
- `repomix-pack.zip` (zip con ambos).

### COMANDO canónico (PowerShell) — copiar/pegar
```powershell
# Evidencia SKB (Nivel estricto) — ejecutar desde la raíz del repo, en la rama del PR
git status
if (git status --porcelain) { throw "WORKTREE NO LIMPIO: commitea o stash antes de generar evidencia" }
$head = (git rev-parse HEAD).Trim()
Set-Content -Path .\repomix-head.txt -Value $head -NoNewline -Encoding ascii
if ((Get-Content .\repomix-head.txt -Raw).Trim() -ne $head) { throw "SHA mismatch en repomix-head.txt" }
Remove-Item .\repomix-output*.xml -ErrorAction SilentlyContinue

npx repomix --style xml --parsable-style --include-full-directory-structure `
  --include "docs/**,src/**,tests/**,scripts/**,.github/**,pyproject.toml,.gitignore,README*,LICENSE*" `
  --ignore  "**/node_modules/**,**/.venv/**,**/.git/**,**/dist/**,**/build/**,**/.tmp_bench/**,**/__pycache__/**,**/.mypy_cache/**,**/.ruff_cache/**,**/.pytest_cache/**,repomix-output*.xml,repomix-*.zip" `
  --split-output 20mb `
  -o .\repomix-output.xml

Select-String -Path .\repomix-output*.xml -Pattern ".github/workflows" -Quiet | % { if (-not $_) { throw "FALTA .github/workflows" } }
Select-String -Path .\repomix-output*.xml -Pattern "pyproject.toml"   -Quiet | % { if (-not $_) { throw "FALTA pyproject.toml" } }
Select-String -Path .\repomix-output*.xml -Pattern ".gitignore"       -Quiet | % { if (-not $_) { throw "FALTA .gitignore" } }

Remove-Item .\repomix-pack.zip -ErrorAction SilentlyContinue
Remove-Item .\repomix-*.zip -ErrorAction SilentlyContinue
Compress-Archive -Force -Path .\repomix-head.txt, .\repomix-output*.xml -DestinationPath .\repomix-pack.zip
"OK repomix-pack.zip => $head"
```

### CHECKS mínimos de integridad (antes de compartir el pack)
- El SHA en `repomix-head.txt` coincide con `git rev-parse HEAD`.
- En `repomix-output*.xml` existen referencias a:
  - `.github/workflows`
  - `pyproject.toml`
  - `.gitignore`

### Regla Antigravity (auditoría previa)
- Para PRs donde Codex cambie código: exigir `git diff --unified=0` pegado en el PR antes del merge.

## Bootstrap reproducible (Codex / agentes / dev local)

Objetivo: ejecutar exactamente lo mismo que CI (deps + comandos) y evitar fallos por `missing httpx` / `pytest-cov`.

### Comando único (deps + herramientas CI)
1. Crear y activar entorno virtual.
2. Instalar dependencias de test **solo** por la vía oficial:
   - Preferido (existe extra dev): `pip install -e ".[dev]"`
   - Alternativa (solo si existiera `requirements-dev.txt`): `pip install -r requirements-dev.txt`
3. El extra `.[dev]` incluye todo lo necesario para CI (incluyendo ruff/mypy si aplica).

Ejemplo Linux/macOS (una sola línea):
```bash
python -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && pip install -e ".[dev]"
```

En Windows usar el script `scripts/bootstrap_codex.ps1`.

### Verificación de paquetes críticos
```bash
python -m pip show httpx
python -m pip show pytest-cov
python -m pip show ruff
python -m pip show mypy
```

### Comandos CI (idénticos a CI)
```bash
pytest -q
pytest --cov=src --cov-fail-under=80
ruff check .
mypy src/
```
