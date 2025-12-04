# Munay: Contrato de Consumo del Módulo de Audio del Bot Neutro

Este documento describe cómo el cliente Munay consume el endpoint `/audio` del Bot Neutro.

## Petición

- **Método**: `POST /audio`
- **Contenido**: `multipart/form-data`
  - Campo obligatorio `file`: archivo de audio
- **Headers obligatorios**:
  - `X-API-Key`
  - `X-Correlation-Id`
  - `x-munay-user-id`
  - `x-munay-context`

## Contextos permitidos

`x-munay-context` admite los valores:

- `diario_emocional`
- `coach_habitos`
- `reflexion_general`

## Mapeo a eventos Munay

El consumo de `/audio` genera un `munay_event` con los siguientes mapeos:

- `diario_emocional` → `journal_entry`
- `coach_habitos` → `habit_coaching`
- `reflexion_general` → `insight`
- El sistema puede marcar `crisis_flag` si el pipeline detecta alerta.

Cada evento se enriquece con `audio_session_id` retornado por el Bot Neutro.

## Respuesta esperada

El backend neutro responde con un JSON que incluye la transcripción, la respuesta generada y la URL pública del TTS. Ejemplo:

```json
{
  "session_id": "uuid-de-la-sesion",
  "corr_id": "corr-id-correlacion",
  "transcript": "texto reconocido",
  "reply_text": "respuesta generada",
  "tts_url": "https://.../tts.wav",
  "usage": {
    "input_seconds": 1.0,
    "output_seconds": 1.5,
    "stt_ms": 123,
    "llm_ms": 456,
    "tts_ms": 200,
    "total_ms": 779,
    "provider_stt": "X",
    "provider_llm": "Y",
    "provider_tts": "Z"
  },
  "meta": {
    "context": "diario_emocional"
  }
}
```

Munay usará `tts_url` como URL pública del audio TTS. En futuras versiones, el cliente puede cachear o descargar este recurso, pero el contrato neutro solo garantiza la URL, no los bytes inline. El cliente también debe propagar `session_id`, `corr_id` y `meta` (incluyendo `meta.context`) en su propio modelo de observabilidad y trazabilidad.
