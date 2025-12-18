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

## NORTE-first (nuevo estándar)
- Toda orden CAMBIAR debe justificar “por qué HOY” (bug reproducible hoy / contrato hoy / desbloqueo hoy).
- Queda prohibido el “futurismo”: hardening/performance/escala “por si acaso” sin evidencia de problema actual.
- Si una mejora es “buena idea” pero no desbloquea el objetivo actual, se mueve a NO IMPLEMENTADO con su desbloqueo.

## Regla anti-bucle
- Máximo 1 ronda de ajustes por orden (una sola iteración).
- Si algo no es bloqueante para el objetivo operativo, NO se corrige en esa orden: se documenta en NO IMPLEMENTADO.

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

## DoD (Definition of Done) — obligatorio
- [ ] `docs/PLANTILLA_ORDEN_EJECUCION_KAIZEN.md` incluye sección “Filtro NORTE-first”.
- [ ] `docs/GOBERNANZA/KAIZEN_GUARDRAILS.md` incluye reglas “NORTE-first”, “anti-bucle”.
- [ ] No se toca código runtime.
- [ ] PR docs-only pasa checks existentes.

## Comandos de verificación — obligatorio
- pytest -q
- pytest --cov=src --cov-fail-under=80

## CI
[CI_REAL] (si aplica)
- (listar SOLO workflows existentes en .github/workflows)

[CI_FUTURO] (no bloqueante)
- Validación automática del “Filtro NORTE-first” (si algún día se implementa en scripts).

## Riesgos y mitigaciones
- Riesgo: “NORTE-first” se interprete como “bajar calidad”.
- Mitigación: Mantener DoD + contracts-first; solo se elimina trabajo no requerido hoy.

## NO IMPLEMENTADO (y por qué)
- Integrar la regla NORTE-first en `scripts/kaizen_validate_order.py`
- Por qué: No es necesario hoy para avanzar; la gobernanza documental basta para el siguiente milestone.
- Riesgo aceptado: Se depende de disciplina humana en el corto plazo.
- Qué lo desbloquea: Cuando haya 3+ órdenes seguidas con desvíos o bucles por futurismo.

## Nota operacional (para Codex / ejecución)
- Esta orden es docs-only.
- No proponer mejoras “por si acaso”.
- Si aparece una idea de hardening/perf: moverla a NO IMPLEMENTADO automáticamente.
- Resultado esperado: desde la próxima orden CAMBIAR, cualquier sugerencia tipo “robustecer parse” o “optimizar por escala futura” queda automáticamente bloqueada por el Filtro NORTE-first a menos que haya bug reproducible hoy o contrato hoy que lo exija.
