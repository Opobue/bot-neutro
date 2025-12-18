# PLANTILLA — ORDEN DE EJECUCIÓN KAIZEN

## Regla de transparencia (obligatoria)
- Todo lo recomendado debe quedar como: IMPLEMENTADO (con diff + evidencia) o NO IMPLEMENTADO (con por qué).
- Prohibido omitir recomendaciones “porque no entraron”.

## Metadata (obligatoria)
NORTE_VERSION_ACTUAL = (copiar exactamente desde docs/02_ESTADO_Y_NORTE.md)
Nivel = {L1|L2|L3}
TIPO = {DESCUBRIR|DECIDIR|CAMBIAR|BLOQUEO}
Basado en = (hilo/ID o PR/Issue + fecha)
Objetivo operativo = (1 frase: “qué cambia observablemente”)
Contratos impactados = (lista de docs/CONTRATO_*.md o “N/A”)

## Objetivo de esta orden:
(una línea, accionable)

## Alcance / Fuera de alcance:
- IN:
- OUT:

## Parches (DIFF) — obligatorios
- Archivo X:

* diff --git ...
*

## DoD (Definition of Done) — obligatorio
- [ ] tests pasan
- [ ] coverage se mantiene
- [ ] contratos no se rompen
- [ ] docs actualizadas

## Comandos de verificación — obligatorio
- pytest -q
- pytest --cov=src --cov-fail-under=80
- (si aplica) ruff check .
- (si aplica) ruff format --check .

## CI
[CI_REAL] (si aplica)
- (listar SOLO workflows existentes en .github/workflows)
Regla: CI_REAL solo puede contener checks que existan hoy. Si no existe workflow, va a CI_FUTURO.

[CI_FUTURO] (no bloqueante)
- (ideas/roadmap, no criterio de DoD)

## Riesgos y mitigaciones
- Riesgo:
- Mitigación:

## NO IMPLEMENTADO (y por qué)
- Item:
- Por qué:
- Riesgo aceptado:
- Qué lo desbloquea:
