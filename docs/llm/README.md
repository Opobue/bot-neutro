# LLM D1 (Pack Mode + Bridge)

Este directorio estandariza el flujo de evidencia para salidas D1 y su verificación mecánica.

## Pack Mode (RepoPack + EvidencePack) — canónico

### Estructura
- `docs/llm/repomix/`: RepoPack **local opcional** (no se versiona).
- `docs/llm/evidence/`: EvidencePack derivado (no versionado).
- `docs/llm/submissions/`: entregables D1 (.md) a validar.
- `docs/llm/RUBRICA_D1.md`: orden y reglas del formato D1.
- `docs/llm/AGENT_EXECUTION_POLICY.md`: política operativa para agentes.

### Flujo canónico (Pack Mode)
1) CI (por defecto): RepoPack se genera en el runner (`/tmp`) y no se versiona.

2) Local (opcional): Generar RepoPack (Repomix) en `docs/llm/repomix/` para auditoría/compartir fuera de CI.

3) Generar EvidencePack (derivado, no versionado):
```bash
python scripts/llm/build_evidence_pack.py \
  --repomix docs/llm/repomix/repomix-output*.xml \
  --head docs/llm/repomix/repomix-head.txt \
  --out docs/llm/evidence
```

4) Validar entregables D1 (linter directo):
```bash
python scripts/llm/lint_d1_output.py docs/llm/submissions/*.md \
  --evidence <ruta_impresa_por_build_evidence_pack>
```

### Validación automática (harness local)
> Nota: el harness local **no genera RepoPack/EvidencePack**. Asume que ya existe un EvidencePack en `docs/llm/evidence/`.

Linux/macOS (bash):
```bash
scripts/llm/validate_llm_d1.sh docs/llm/submissions/mi_envio.md
```

Windows (PowerShell):
```powershell
.\scripts\llm\validate_llm_d1.ps1 docs/llm/submissions/mi_envio.md
```

### Reglas clave
- La Fuente Única es el RepoPack; si no está en el pack, no existe.
- El EvidencePack solo sirve para verificación mecánica; no se commitea.
- El linter falla si falta evidencia, hay rangos inválidos o se viola la rúbrica.

## Bridge Mode (EVIDENCIA_TXT -> SHA256) — opcional

Bridge existe porque los LLMs no citan líneas/hashes consistentemente. Permite citar “texto humano” y convertirlo determinísticamente a evidencia criptográfica.

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
