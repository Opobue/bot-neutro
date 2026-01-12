# Protocolo reproducible — Bridge Mode (EVIDENCIA_TXT -> SHA256)

Objetivo: dejar un protocolo reproducible para usar/probar/demostrar el PR “Bridge Mode (EVIDENCIA_TXT -> SHA256)” y validar que funciona en Windows (PowerShell) y en Bash (WSL/Git-Bash), sin modificar README.

## Contexto
- Bridge ya pasó validación vía `validate_llm_d1.ps1 -Bridge`.
- Existe un fallo local al ejecutar `bridge_d1.py` sobre fixtures: `Archivo no encontrado: scripts\llm\_fixtures\bridge_example.md`.
- Debemos confirmar si es un problema de ruta/sync/branch y dejar el protocolo de pruebas.

## Paso 1 — Precheck (PowerShell)
Ejecutar:

```powershell
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --porcelain
Test-Path .\scripts\llm\bridge_d1.py
Test-Path .\scripts\llm\_fixtures\bridge_example.md
Test-Path .\scripts\llm\_fixtures\bridge_evidence.txt
Get-ChildItem .\scripts\llm -Recurse -Filter "bridge_example.md" | Select-Object FullName
```

**Criterio PASS**
- `bridge_d1.py` existe.
- Si los fixtures no existen: **no es bug del bridge**, es un tema de sync/branch.

## Paso 2 — Si faltan fixtures (PowerShell)
Ejecutar:

```powershell
git fetch origin
git pull --ff-only
# Si aplica:
git switch develop
git pull --ff-only
```

Repetir los `Test-Path` de fixtures.

**Criterio PASS**
- Los fixtures aparecen.

## Paso 3 — Prueba canónica Windows (PowerShell)
Ejecutar:

```powershell
.\scripts\llm\validate_llm_d1.ps1 "docs\llm\submissions\diagnostico_inicial_bridge.md" -Bridge
echo $LASTEXITCODE
```

**Criterio PASS**
- Imprime `✅ VALIDATION PASS`.
- `LASTEXITCODE=0`.

**Evidencia a guardar**
- `docs\llm\submissions\diagnostico_inicial_bridge.md.bridge.md` (artefacto bridged).

## Paso 4 — Prueba Bridge directa (PowerShell, sin linter)
Ejecutar:

```powershell
python .\scripts\llm\bridge_d1.py .\scripts\llm\_fixtures\bridge_example.md --root . --out .\scripts\llm\_fixtures\bridge_example.bridge.md
type .\scripts\llm\_fixtures\bridge_example.bridge.md
```

**Criterio PASS**
- El output contiene `(EVIDENCIA: …#SHA256:…)`.

## Paso 5 — Prueba Bash (Windows con Git-Bash o WSL)
Ejecutar desde PowerShell:

```powershell
bash scripts/llm/validate_llm_d1.sh docs/llm/submissions/diagnostico_inicial_bridge.md --bridge
echo $LASTEXITCODE
```

**Criterio PASS**
- `LASTEXITCODE=0`.

## Salida esperada de la orden
- Confirmación de existencia de fixtures o diagnóstico de sync/branch.
- Captura/registro del PASS en Windows (PowerShell).
- Captura/registro del PASS en Bash.
- Artefacto bridged generado y verificable.
