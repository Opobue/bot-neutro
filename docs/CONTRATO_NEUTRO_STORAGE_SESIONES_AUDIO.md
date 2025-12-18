# Contrato Neutro de Storage de Sesiones de Audio

Este documento describe el esquema y las operaciones mínimas para persistir sesiones de audio procesadas por el Bot Neutro.

## Entidad `audio_session`

| Campo                     | Tipo / Notas                                           |
| ------------------------- | ------------------------------------------------------ |
| `id`                      | Identificador interno (UUID recomendado).             |
| `corr_id`                 | Correlation ID externo recibido en la petición.       |
| `api_key_id`              | Identificador lógico de la API key usada.             |
| `user_external_id`        | Identificador del usuario en el cliente.              |
| `created_at`              | Timestamp de creación.                                |
| `expires_at`              | Timestamp de expiración (`created_at` + `retention_days`). |
| `request_mime_type`       | MIME type del audio de entrada.                       |
| `request_duration_seconds`| Duración aproximada del audio de entrada.             |
| `transcript`              | Texto transcrito (STT).                               |
| `reply_text`              | Texto de respuesta (LLM).                             |
| `tts_available`           | Booleano indicando si hay audio TTS disponible.       |
| `tts_storage_ref`         | Referencia (URL/path) al audio TTS persistido.        |
| `usage_stt_ms`            | Milisegundos consumidos en STT.                       |
| `usage_llm_ms`            | Milisegundos consumidos en LLM.                       |
| `usage_tts_ms`            | Milisegundos consumidos en TTS.                       |
| `usage_total_ms`          | Milisegundos totales del pipeline.                    |
| `provider_stt`            | Proveedor STT usado.                                  |
| `provider_llm`            | Proveedor LLM usado.                                  |
| `provider_tts`            | Proveedor TTS usado.                                  |
| `meta_tags`               | Diccionario de etiquetas libres (string → string).    |

## Operaciones mínimas

- `create(audio_session)`: persiste la sesión completa y calcula `expires_at` según la política de retención vigente.
- `list_by_api_key(api_key_id, limit, offset, api_key_id_autenticada)`: lista sesiones por API key ordenadas por `created_at DESC` **solo si** `api_key_id == api_key_id_autenticada`.
- `list_by_user(user_external_id, limit, offset, api_key_id_autenticada)`: lista sesiones por usuario ordenadas por `created_at DESC` **solo** para sesiones cuyo `api_key_id` coincide con `api_key_id_autenticada`.
- Si `api_key_id_autenticada` es `None`, la operación debe fallar con `AccessDeniedError` (o equivalente de la implementación).

## Política de privacidad y seguridad

El almacenamiento de sesiones debe cumplir **obligatoriamente** con la política definida en `docs/CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md`.

## Índices recomendados

- Índice compuesto: `(user_external_id, created_at DESC)`.
- Índice compuesto: `(api_key_id, created_at DESC)`.
- Índice único en `corr_id`.
