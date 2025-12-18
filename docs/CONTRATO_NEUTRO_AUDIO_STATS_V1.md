# CONTRATO_NEUTRO_AUDIO_STATS_V1

## Propósito
Exponer **estadísticas agregadas** del pipeline de audio por tenant (API key), sin permitir lectura/listado de sesiones ni fuga de PII.

## Endpoint
`GET /audio/stats`

### Autenticación
- Requiere `X-API-Key` válida.
- Multi-tenant estricto: responde **solo** con agregados del tenant autenticado.

### Respuesta 200 (JSON)
Campos mínimos:
- `api_key_id`: string (ID derivado; NO es el secreto `X-API-Key`; se usa `sha256(X-API-Key)` en hex y se trunca a 12 chars)
- `totals`:
  - `sessions_current`: int (conteo inspeccionado para el agregado; puede estar capado por `AUDIO_STATS_MAX_SESSIONS`)
  - `limit_applied`: int (valor efectivo aplicado como cap)
  - `sessions_purged_total`: int (contador acumulado del runtime, no por-tenant)
- `by_provider`:
  - `stt`: { "<provider_id>": int }
  - `llm`: { "<provider_id>": int }
  - `tts`: { "<provider_id>": int }

### Prohibiciones (privacidad)
Este endpoint **NO PUEDE** devolver (directa o indirectamente):
- `transcript`, `reply_text`, `meta_tags`, `user_external_id`, `corr_id`, `tts_storage_ref`
- listas de sesiones, ids de sesión ni detalles por sesión

### Errores
- 401 si falta/invalid `X-API-Key` (según el comportamiento actual del core).

## Dependencias
- Debe cumplir `docs/CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md`.
- No desbloquea endpoints de lectura/listado de sesiones.
