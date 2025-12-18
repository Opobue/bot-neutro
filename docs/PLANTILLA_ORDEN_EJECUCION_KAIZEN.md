# PLANTILLA — ORDEN DE EJECUCIÓN KAIZEN

## Regla de transparencia (obligatoria)
- Todo lo recomendado debe quedar como: IMPLEMENTADO (con diff + evidencia) o NO IMPLEMENTADO (con por qué).
- Prohibido omitir recomendaciones “porque no entraron”.

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

## Riesgos y mitigaciones
- Riesgo:
- Mitigación:

## NO IMPLEMENTADO (y por qué)
- Item:
- Por qué:
- Riesgo aceptado:
- Qué lo desbloquea:
