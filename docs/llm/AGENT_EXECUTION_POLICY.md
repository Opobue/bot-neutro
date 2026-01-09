# AGENT_EXECUTION_POLICY (LLM Pack Mode)

Esta política actúa como instrucción operativa versionada para cualquier agente que genere salidas D1.

## Principios
- **Pack Mode obligatorio**: RepoPack (Repomix) es la única fuente de verdad.
- **EvidencePack derivado**: se usa solo para verificación mecánica; no se versiona.
- **No inventar**: si un dato no está en el RepoPack, usar `[DESCONOCIDO]`.
- **No mezclar fases**: D1 (DESCUBRIR) no incluye cambios ni decisiones de implementación.

## Evidencia
- Toda afirmación marcada como `HECHO:` debe citar evidencia válida en el formato definido en `docs/llm/RUBRICA_D1.md`.
- Las citas deben referenciar rutas y rangos reales del RepoPack.

## Gate D1→D2
- Siempre incluir TOP 3 Bloqueos, TOP 3 Riesgos Antigravity y TOP 3 Oportunidades.
- No usar “Ninguno probado” como bypass.
- Mantener mínimo 3 ítems en cada TOP 3, aun con `[DESCONOCIDO]`.
