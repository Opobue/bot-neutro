# LLM Pack Mode (RepoPack + EvidencePack)

Este directorio estandariza el flujo de evidencia para salidas D1 y su verificación mecánica.

## Estructura
- `docs/llm/repomix/`: RepoPack **local opcional** (no se versiona).
- `docs/llm/evidence/`: EvidencePack derivado (no versionado).
- `docs/llm/submissions/`: entregables D1 (.md) a validar.
- `docs/llm/RUBRICA_D1.md`: orden y reglas del formato D1.
- `docs/llm/AGENT_EXECUTION_POLICY.md`: política operativa para agentes.

## Flujo canónico (Pack Mode)
1) CI (por defecto): RepoPack se genera en el runner (`/tmp`) y no se versiona.

2) Local (opcional): Generar RepoPack (Repomix) en `docs/llm/repomix/` para auditoría/compartir fuera de CI:
```bash
# Genera repomix-output*.xml y repomix-head.txt en docs/llm/repomix/
# (ver contrato: docs/CONTRATO_NEUTRO_CONTRIBUCION.md)
```

3) Generar EvidencePack (derivado, no versionado):
```bash
python scripts/llm/build_evidence_pack.py \
  --repomix docs/llm/repomix/repomix-output*.xml \
  --head docs/llm/repomix/repomix-head.txt \
  --out docs/llm/evidence
```

4) Validar entregables D1:
```bash
python scripts/llm/lint_d1_output.py docs/llm/submissions/*.md \
  --evidence <ruta_impresa_por_build_evidence_pack>
```

## Reglas clave
- La Fuente Única es el RepoPack; si no está en el pack, no existe.
- El EvidencePack solo sirve para verificación mecánica; no se commitea.
- El linter falla (exit 2) si falta evidencia, hay rangos inválidos o se viola la rúbrica.
