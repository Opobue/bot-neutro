# LLM D1

## Bridge Mode

### Formato EVIDENCIA_TXT

```
(EVIDENCIA_TXT: ruta "snippet")
```

### Flujo 1–5

1. El LLM emite `(EVIDENCIA_TXT: ruta "snippet")`.
2. `bridge_d1.py` busca la línea exacta `snippet` en el archivo `ruta` (match por `line.strip()`).
3. Calcula `sha256(snippet.strip().encode("utf-8"))`.
4. Reescribe la marca como `(EVIDENCIA: ruta#SHA256:<hash>)`.
5. El linter se ejecuta sobre el archivo convertido.

**Nota:** Bridge es un preprocesador: convierte `EVIDENCIA_TXT -> EVIDENCIA:#SHA256` y luego corre el linter estándar.
Requiere EvidencePack en `docs/llm/evidence/` (generado por el flujo actual).

### Ejecución Bash

```bash
python scripts/llm/bridge_d1.py <input_md> --root <repo_root> --out <output_md>
python scripts/llm/validate_llm_d1.sh <submission_md> --bridge
```

### Ejecución PowerShell

```powershell
python scripts/llm/bridge_d1.py <input_md> --root <repo_root> --out <output_md>
./scripts/llm/validate_llm_d1.ps1 <submission_md> -Bridge
```

### Prueba manual mínima (sin framework)

Archivo de ejemplo:

```
scripts/llm/_fixtures/bridge_example.md
```

Comando (Bash):

```bash
python scripts/llm/bridge_d1.py scripts/llm/_fixtures/bridge_example.md \
  --root . \
  --out scripts/llm/_fixtures/bridge_example.bridge.md
```

Comando (PowerShell):

```powershell
python scripts/llm/bridge_d1.py scripts/llm/_fixtures/bridge_example.md \
  --root . \
  --out scripts/llm/_fixtures/bridge_example.bridge.md
```
