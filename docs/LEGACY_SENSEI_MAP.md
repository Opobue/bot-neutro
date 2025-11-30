# Mapa de código legacy de SenseiKaizen

| Ruta | Rol actual | ¿Usado por el Bot Neutro HTTP? | Prioridad para limpieza | Notas | Fase sugerida | Acción objetivo |
| --- | --- | --- | --- | --- | --- | --- |
| `src/sensei/config.py` | Configuración histórica con validaciones y helpers ligados al bot original (Notion, Google, scheduler, etc.). | Dudoso (se usa por compatibilidad en algunos tests pero no es la fuente principal del HTTP neutro). | Alta | Requiere separar constantes neutras de credenciales y lógicas heredadas; mover a paquete específico o eliminar en favor de `settings.py`. | F2/F3 | Refactor para separar settings neutros de lógica legacy; no borrar de golpe. |
| `src/sensei/integrations/notion_wrapper.py` | Shim que bloquea la antigua integración con Notion. | No | Alta | Mantener aislado; mover a repositorio de bot específico o borrar cuando se elimine dependencia. | F3 | Mover a repo legacy de integraciones externas. |
| `src/sensei/integrations/supabase_wrapper.py` | Accesos directos a tablas de Supabase para hábitos/compras/entregables. | No | Alta | Candidato a extracción completa a bot específico; requiere tests dedicados si se mantiene. | F3 | Extraer a módulo opcional para hábitos/compras. |
| `src/sensei/services/gcal.py` | Cliente de Google Calendar (service account) usado por el bot viejo. | No | Media | Puede moverse a proveedor opcional; actualmente sin uso en rutas HTTP neutras. | F3 | Mover a paquete gcal opcional o repo aparte. |
| `src/sensei/calendar_utils.py` | Stubs de utilidades de Calendar para compatibilidad con código antiguo. | No | Media | Extraíble junto con `services/gcal.py` una vez se eliminen dependencias. | F3 | Mover a paquete gcal opcional o repo aparte. |
| `src/sensei/schedule_utils.py` | Helper de scheduling (APScheduler) para check-ins heredados. | No | Media | No usado por el contrato HTTP; se puede aislar o eliminar tras confirmar ausencia en runtimes. | F3 | Extraer o eliminar tras validar que no impacta Bot Neutro. |
| `gcal_utils.py` | Wrapper de conveniencia que recarga el servicio de Calendar legacy. | No | Media | Dependencia auxiliar de `services/gcal.py`; mover junto con integración o retirar. | F3 | Mover a paquete gcal opcional o repo aparte. |
| `tests/__init__.py` | Bootstrap de pruebas con stubs de Notion, APScheduler, Rich y rate limit para el stack legacy. | Dudoso | Media | Mezcla configuraciones neutras con soportes legacy; dividir fixtures cuando se separe el código. | F2/F3 | Refactor de fixtures para separar neutral vs legacy. |
| `tests/unit/test_config_extra.py` | Cobertura de la configuración heredada en `config.py`. | No | Media | Podría migrarse a suite de bot específico o eliminarse tras retirar `config.py`. | F2/F3 | Mover a suite legacy o eliminar tras refactor de config. |
| `tests/unit/test_check_config_modes.py` | Valida restricciones legacy (modos TTS/STT en `config.py`). | No | Media | Se puede eliminar junto con la configuración heredada. | F2/F3 | Mover a suite legacy o eliminar cuando se retire config. |
| `tests/unit/test_supabase_wrapper.py` | Verifica que los accesos Supabase legacy devuelven listas. | No | Alta | Depende directamente de integración legacy; remover al extraer Supabase. | F3 | Mover a suite de tests legacy; no requerido por Bot Neutro. |
| `tests/integration/test_supabase.py` | Smoke test de la integración Supabase legacy. | No | Alta | Igual que el unitario: mover o eliminar con la integración. | F3 | Mover a suite de tests legacy; no requerido por Bot Neutro. |
| `tests/unit/test_gcal_utils.py` | Pruebas del wrapper de Google Calendar legacy. | No | Media | Remover al extraer gcal. | F3 | Mover a suite legacy o eliminar con la extracción gcal. |
| `tests/unit/test_report_daily.py` | Valida script legacy de reportes diarios sobre base SQLite. | No | Media | Asociado a pipelines heredados; evaluar si se mantiene en repositorio aparte. | F4 | Mantener solo si se preserva el pipeline legacy de reportes; de lo contrario, eliminar. |

Las columnas "Fase sugerida" y "Acción objetivo" se alinean con
[NEUTRO_MIGRATION_PLAN](./NEUTRO_MIGRATION_PLAN.md) y sirven como guía
para futuras órdenes Kaizen de limpieza. Esta orden L5 no mueve ni elimina
ningún archivo; solo documenta el plan.
