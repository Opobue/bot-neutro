# CONTRATO_API_PUBLICA_V1 – Endpoint /audio

Este documento define el contrato público de la API de voz del Bot Neutro
para la versión v1. Esta API está pensada para ser consumida por:

Este contrato describe el comportamiento **actual** del endpoint `/audio`:
no introduce cambios nuevos, solo congela como oficial lo que ya está
implementado y probado.

- La app Munay (primer cliente oficial).
- Otros proyectos propios del autor.
- Clientes externos (empresas, integradores n8n/Make, etc.).

## Visión general de `/audio`

- Método: `POST`
- Path: `/audio`
- Auth: header `X-API-Key` obligatorio.
- Formato: `multipart/form-data` con un solo campo de archivo.

## Headers

- `X-API-Key` (obligatorio)
  - Clave que identifica al cliente de la API (tenant).
  - En el estado actual del proyecto se asume una única key fija
    (`changeme` en desarrollo), pero el diseño está preparado para
    múltiples clientes y planes.

- `x-munay-llm-tier` (opcional, case-insensitive)
  - Valores aceptados: `freemium`, `premium`.
  - Default: `freemium` si falta o es inválido.
  - Controla la tier lógica del LLM (modelo económico vs modelo premium).

## Body (multipart/form-data)

- Campo: `audio_file` (obligatorio)
  - Tipo: archivo binario.
  - Content-Type recomendado: `audio/wav` (mono, 16 kHz o similar).
  - Tamaño máximo: depende de límites de despliegue (no fijados aún
    en este contrato, se documentarán cuando haya límites comerciales).

## Respuesta 200 OK (JSON)

```json
{
  "session_id": "uuid",
  "corr_id": "uuid",
  "transcript": "Texto transcrito del audio de entrada",
  "reply_text": "Texto de respuesta generado por el LLM (o stub)",
  "tts_url": "https://.../audio.wav",
  "usage": {
    "input_seconds": 1.0,
    "output_seconds": 1.5,
    "stt_ms": 100,
    "llm_ms": 200,
    "tts_ms": 150,
    "total_ms": 450,
    "provider_stt": "azure-stt",
    "provider_llm": "openai-llm|stub-llm",
    "provider_tts": "azure-tts"
  },
  "meta": null
}
```

Donde:

* `session_id`: identificador de sesión de audio.
* `corr_id`: identificador de correlación para logs/observabilidad.
* `transcript`: transcripción final entendida por el sistema.
* `reply_text`: respuesta textual final (LLM o stub).
* `tts_url`: URL (si hay audio de respuesta generado) o `null`.
* `usage.*`: métricas de tiempo y proveedores efectivos utilizados.
* `meta`: reservado para extensiones futuras (por ahora `null`).

## Errores

- `401 Unauthorized`
  - Cuando falta `X-API-Key` o no es válida.
- `422 Unprocessable Entity`
  - Cuando falta el campo `audio_file` o el formato es inválido.
- `5xx`
  - Errores internos inesperados. El objetivo del diseño es que
    problemas externos (cuota del LLM, proveedor de voz) se traduzcan
    en degradación controlada (uso del stub) manteniendo `200 OK`
    siempre que sea posible.

## Multi-tenant y planes

- El diseño de la API asume que cada `X-API-Key` identifica a un cliente
  (tenant). El sistema puede, en el futuro, aplicar:
  - límites por cliente (QPS, segundos de audio, tokens),
  - planes Free / Pro / Enterprise.
- Aunque el código actual usa una sola key fija en desarrollo,
  este contrato se escribe ya pensando en:
  - Munay como primer cliente oficial,
  - otros proyectos propios del autor,
  - clientes externos.

## Ejemplos de uso (curl)

### Llamada estándar freemium

```bash
curl -X POST \
  -H "X-API-Key: changeme" \
  -H "x-munay-llm-tier: freemium" \
  -F "audio_file=@/ruta/a/audio.wav" \
  http://localhost:8000/audio
```

### Llamada con tier premium

```bash
curl -X POST \
  -H "X-API-Key: changeme" \
  -H "x-munay-llm-tier: Premium" \
  -F "audio_file=@/ruta/a/audio.wav" \
  http://localhost:8000/audio
```
