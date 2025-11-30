# Contrato Neutro de API HTTP

Este contrato define las rutas HTTP base del Bot Neutro. Cualquier bot derivado debe preservar rutas, semántica y headers básicos.

Los endpoints `/text` y `/actions` son opcionales: forman parte del contrato recomendado del Bot Neutro, pero una implementación mínima puede omitirlos siempre que preserve `/healthz`, `/readyz`, `/version`, `/metrics` y `/audio`.

## Endpoints core

### `/healthz`
- **Método**: `GET`
- **Objetivo**: Comprobación de salud básica.
- **Headers relevantes**: `X-Correlation-Id` opcional para trazabilidad.
- **Response (200)**:
```
{}
```

### `/readyz`
- **Método**: `GET`
- **Objetivo**: Verifica dependencias mínimas para readiness.
- **Headers relevantes**: `X-Correlation-Id` opcional.
- **Response (200)**:
```
{}
```

### `/version`
- **Método**: `GET`
- **Objetivo**: Exponer versión desplegada.
- **Headers relevantes**: `X-Correlation-Id` opcional.
- **Response (200)** (ejemplo simplificado):
```
{"version": "<hash|tag>"}
```

### `/metrics`
- **Método**: `GET`
- **Objetivo**: Exponer métricas Prometheus.
- **Headers relevantes**: `content-type: text/plain; version=0.0.4; charset=utf-8`
- **Response (200)**: payload Prometheus con métricas como `sensei_request_latency_seconds_bucket`.

### `/audio`
- **Método**: `POST`
- **Objetivo**: Procesar audio entrante (STT → LLM → TTS si aplica).
- **Headers relevantes**:
  - `X-API-Key` si la autenticación está habilitada.
  - `X-Correlation-Id` para trazabilidad.
  - `X-Outcome` / `X-Outcome-Detail` en la respuesta para estado.
- **Request** (`multipart/form-data`):
```
----boundary
Content-Disposition: form-data; name="file"; filename="sample.wav"
Content-Type: audio/wav

<bytes>
----boundary--
```
- **Response (200)** (ejemplo simplificado):
```
{
  "transcript": "hola mundo",
  "reply_text": "respuesta generada",
  "audio_url": "https://.../tts.wav"
}
```

### `/text` (si está disponible)
- **Método**: `POST`
- **Objetivo**: Procesar texto directo a través del LLM.
- **Headers relevantes**: `X-API-Key`, `X-Correlation-Id`, `X-Outcome`.
- **Request** (ejemplo simplificado):
```
{"message": "hola"}
```
- **Response (200)**:
```
{"reply_text": "respuesta generada"}
```

### `/actions` (si está disponible)
- **Método**: `POST`
- **Objetivo**: Ejecutar acciones externas derivadas del LLM.
- **Headers relevantes**: `X-API-Key`, `X-Correlation-Id`, `X-Outcome`.
- **Request** (ejemplo simplificado):
```
{
  "action": "call_webhook",
  "payload": {"foo": "bar"}
}
```
- **Response (200)**:
```
{"status": "accepted"}
```

## Semántica de headers y contratos relacionados
- Los headers estándar están definidos en [CONTRATO_NEUTRO_HEADERS](./CONTRATO_NEUTRO_HEADERS.md).
- Observabilidad y métricas del endpoint `/metrics` se detallan en [CONTRATO_NEUTRO_OBSERVABILIDAD](./CONTRATO_NEUTRO_OBSERVABILIDAD.md).
- Reglas de rate limit aplicables a `/audio`, `/text` y `/actions` se describen en [CONTRATO_NEUTRO_RATE_LIMIT](./CONTRATO_NEUTRO_RATE_LIMIT.md).

## Compatibilidad con tests actuales
- Las rutas `/healthz`, `/readyz`, `/version`, `/metrics` y `/audio` coinciden con las verificadas por los tests existentes.
- El `content-type` del endpoint `/metrics` se alinea con las aserciones de la suite de métricas.
- La inclusión de `X-Outcome` y `X-Outcome-Detail` refleja los checks de rate limit y manejo de errores sin modificar código en `src/`.
