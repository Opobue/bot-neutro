# Contrato Neutro de Headers

Los headers estándar aseguran trazabilidad y uniformidad en las respuestas del Bot Neutro y sus derivados.

## Headers principales
- **`X-Outcome`**: estado general de la respuesta. Valores esperados: `ok` | `error`.
- **`X-Outcome-Detail`**: contexto adicional cuando `X-Outcome=error` (ej.: `rate_limit`, `provider_failure`, `validation_error`).
- **`X-Correlation-Id`**: identificador de trazabilidad propagado entre servicios y logs.

### Semántica de `X-Outcome` y `X-Outcome-Detail`

- `X-Outcome` **es obligatorio** en todas las respuestas:
  - `ok` para respuestas 2xx.
  - `error` para respuestas 4xx y 5xx.

- `X-Outcome-Detail` **solo se incluye cuando `X-Outcome=error`**:
  - Debe contener una clave estable de error (ej.: `audio.bad_request`, `auth.unauthorized`, `audio.stt_error`).
  - No se envía en respuestas 2xx por defecto.

- En consecuencia:
  - Las respuestas exitosas (`2xx`) del Bot Neutro exponen `X-Outcome: ok` y **no incluyen** `X-Outcome-Detail`.
  - Cualquier error manejado debe exponer `X-Outcome: error` junto con un `X-Outcome-Detail` específico según el contrato correspondiente (audio, auth, rate-limit, etc.).

## Uso en middleware y endpoints
- Todos los endpoints deben preservar estos headers, incluidos los añadidos por bots derivados.
- En logs JSON estructurados, el valor de `X-Correlation-Id` se representa en el campo `corr_id`, usado para correlacionar trazas y métricas.
- En respuestas 429 por rate limit, `X-Outcome` se fija en `error` y `X-Outcome-Detail` en `rate_limit`.

## Compatibilidad con tests actuales
- Los tests de rate limit verifican la presencia de `X-Outcome` y `X-Outcome-Detail` en respuestas 429.
- La propagación de `X-Correlation-Id` mantiene la trazabilidad usada por las pruebas de métricas y logging.
- No se altera ninguna ruta ni lógica existente, manteniendo `pytest -q` y `pytest -k metrics -q` en verde.
