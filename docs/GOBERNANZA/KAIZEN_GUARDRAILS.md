# KAIZEN_GUARDRAILS
## ¿Qué es una orden verificable?
- Usa la plantilla oficial (`docs/PLANTILLA_ORDEN_EJECUCION_KAIZEN.md`) y conserva todas las secciones obligatorias.
- Declara explícitamente qué quedó IMPLEMENTADO y qué quedó NO IMPLEMENTADO, con su porqué.
- Incluye evidencia rastreable (comandos, tests, rutas de archivos) para cada recomendación.

## Criterios de aceptación mínimos
- Al menos un bloque `diff --git` describiendo los parches solicitados.
- DoD explícito con comandos mínimos (pytest + coverage) y evidencia esperada.
- Secciones presentes: Metadata, Objetivo, Alcance, Parches, DoD, Comandos de verificación, CI, Riesgos, NO IMPLEMENTADO.
- CI_REAL solo menciona workflows existentes; cualquier hipótesis va en CI_FUTURO.

## Reglas
### Regla 1 — Diffs obligatorios
Toda orden CAMBIAR debe incluir al menos 1 bloque `diff --git`.
### Regla 2 — DoD y comandos obligatorios
Debe declarar DoD y comandos mínimos (pytest + coverage).
### Regla 3 — Transparencia
Toda recomendación debe quedar en IMPLEMENTADO o NO IMPLEMENTADO.
### Regla 4 — No inventar
CI_REAL solo enumera workflows existentes. Si no se verifica, va en CI_FUTURO.
### Regla 5 — Evidencia
Cada cambio debe enlazar evidencia: tests/paths/comandos ejecutados.
