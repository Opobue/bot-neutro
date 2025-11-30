# Plan de migración: Bot Neutro vs código legacy SenseiKaizen

Este documento define las fases para migrar el repositorio actual
hacia un Bot Neutro limpio, separando el código legacy específico
de SenseiKaizen sin romper el contrato HTTP ni la suite de tests.

## Fases de migración (alto nivel)

- **Fase 0 — Estado actual (ahora)**
  - Bot Neutro definido por los contratos `NEUTRO_*` y `CONTRATO_NEUTRO_*`.
  - Código legacy etiquetado con comentarios `LEGACY_NEUTRO` / `LEGACY_NEUTRO (MIXTO)`.
  - Ninguna funcionalidad legacy ha sido eliminada.

- **Fase 1 — Aislar dependencias legacy en el mapa**
  - Usar `LEGACY_SENSEI_MAP.md` como fuente de verdad de qué es legacy.
  - Marcar en el mapa el destino previsto de cada módulo (eliminar, mover a repo aparte, mantener como opcional).
  - No tocar aún los módulos; solo actualizar documentación.

- **Fase 2 — Clonar Bot Neutro mínimo en nuevo repo**
  - Usar `NEUTRO_STARTER_KIT.md` como guía para crear un repo nuevo con solo:
    - Core HTTP (`/healthz`, `/readyz`, `/version`, `/metrics`, `/audio`).
    - Middleware, métricas y settings requeridos por el contrato neutro.
  - Excluir cualquier módulo marcado como `LEGACY_NEUTRO` salvo que se documente lo contrario.

- **Fase 3 — Extraer integraciones legacy**
  - Mover integraciones como Supabase, Notion, Google Calendar y schedulers a:
    - Un repo “sensei-legacy”, o
    - Un paquete opcional, documentado como extensión.
  - Ajustar los tests para que el Bot Neutro no dependa de esas integraciones.

- **Fase 4 — Limpieza final del repo original**
  - Una vez el clon Neutro tenga CI/test en verde, decidir:
    - Si el repo actual se congela como legacy.
    - O si se hace limpieza final (remover archivos legacy de este mismo repo).

## Criterios para decidir qué es “Neutro” vs “Legacy”

- Es **Neutro** si:
  - Lo referencian los contratos `CONTRATO_NEUTRO_*`.
  - Es necesario para `/healthz`, `/readyz`, `/version`, `/metrics`, `/audio`.
  - Lo cubren tests que validan el contrato HTTP/observabilidad.

- Es **Legacy** si:
  - Está etiquetado con `LEGACY_NEUTRO`.
  - Depende de integraciones concretas: Notion, Supabase, Google Calendar, APScheduler de check-ins antiguos, scripts de reportes diarios, etc.
  - No es requerido por el Bot Neutro ni por los tests de contratos neutros.

## Reglas de seguridad antes de tocar código legacy

- No borrar módulos legacy sin antes:
  - Quitar sus tests o moverlos a otro repo.
  - Confirmar que `pytest -q` sigue en verde.
- No modificar endpoints `/healthz`, `/readyz`, `/version`, `/metrics`, `/audio` sin actualizar primero los contratos `CONTRATO_NEUTRO_*`.
- Cualquier cambio que afecte a legacy debe referenciar explícitamente:
  - `LEGACY_SENSEI_MAP.md`
  - `NEUTRO_MIGRATION_PLAN.md`

## Compatibilidad con la suite actual

Este plan de migración es solo documental.
No introduce cambios en `src/` ni en la configuración de tests.
Después de crear y mantener este archivo, los comandos
`pytest -q` y `pytest -k metrics -q` deben seguir pasando en verde.
