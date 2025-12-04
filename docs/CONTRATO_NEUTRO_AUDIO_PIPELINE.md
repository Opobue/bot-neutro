# Contrato Neutro de Audio Pipeline

## Descripción general

La interfaz `/audio` del Bot Neutro conecta el pipeline de procesamiento de audio (STT → LLM → TTS) con los consumidores externos. Este contrato detalla los tipos lógicos, la interfaz esperada y el mapeo de errores a respuestas HTTP.

## Tipos lógicos

```python
class AudioRequestContext(TypedDict):
    corr_id: str
    api_key_id: str
    raw_audio: bytes
    mime_type: str
    language_hint: str | None
    client_metadata: dict[str, str] | None

class UsageMetrics(TypedDict):
    input_seconds: float
    output_seconds: float
    stt_ms: int
    llm_ms: int
    tts_ms: int
    total_ms: int
    provider_stt: str
    provider_llm: str
    provider_tts: str

class AudioResponseContext(TypedDict):
    transcript: str
    reply_text: str
    tts_url: str | None
    usage: UsageMetrics
    session_id: str | None
    corr_id: str | None
    meta: dict[str, str] | None

class PipelineError(TypedDict):
    code: str
    message: str
    details: dict[str, str] | None
```

## Interfaz

```python
class AudioPipeline(Protocol):
    def process(self, ctx: AudioRequestContext) -> AudioResponseContext | PipelineError:
        ...
```

## Mapeo de errores a HTTP

| `PipelineError.code`       | HTTP status | `X-Outcome` | `X-Outcome-Detail`         |
| -------------------------- | ----------- | ----------- | -------------------------- |
| `bad_request`              | 400         | `error`     | `audio.bad_request`        |
| `unsupported_media_type`   | 415         | `error`     | `audio.unsupported_media_type` |
| `unauthorized`             | 401         | `error`     | `auth.unauthorized`        |
| `stt_error`                | 502         | `error`     | `audio.stt_error`          |
| `llm_error`                | 502         | `error`     | `audio.llm_error`          |
| `tts_error`                | 502         | `error`     | `audio.tts_error`          |
| `provider_timeout`         | 504         | `error`     | `audio.provider_timeout`   |
| `storage_error`            | 503         | `error`     | `audio.storage_error`      |
| `internal_error`           | 500         | `error`     | `audio.internal_error`     |

## Semántica de respuestas

En el endpoint `/audio`, la `AudioPipeline` se serializa a HTTP con los siguientes criterios:

- Respuestas exitosas:
  - `200 OK`
  - `X-Outcome: success`
  - `X-Outcome-Detail: audio_processed`

  `audio_processed` indica que el audio fue aceptado, procesado por el stub (STT → LLM → TTS) y que la respuesta incluye `session_id`, `corr_id`, `tts_url`, `usage` y `meta` según se describe en este contrato.

- Respuestas de error (`4xx` / `5xx`):

  - `X-Outcome: error`
  - `X-Outcome-Detail` debe ser uno de los códigos de la tabla anterior
    (`audio.bad_request`, `audio.unsupported_media_type`,
    `auth.unauthorized`, `audio.stt_error`, `audio.llm_error`,
    `audio.tts_error`, `audio.provider_timeout`, `audio.storage_error`,
    `audio.internal_error`, etc.).

Otros endpoints del Bot Neutro pueden usar `X-Outcome: ok` en 2xx si así se define en sus respectivos contratos, pero para `/audio` el valor canónico en éxito es `success` con `X-Outcome-Detail: audio_processed`.

### Ejemplo de respuesta exitosa

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
    "provider_stt": "stub-stt",
    "provider_llm": "stub-llm",
    "provider_tts": "stub-tts"
  },
  "meta": {
    "context": "diario_emocional"
  }
}
```

### Campos de `AudioResponseContext`

- `transcript: str`: transcripción STT del audio de entrada.
- `reply_text: str`: texto de respuesta generado por el LLM.
- `tts_url: str | None`: URL pública donde el cliente puede obtener el audio TTS.
- `usage: UsageMetrics`: métricas de uso incluyendo `input_seconds` (audio de entrada) y `output_seconds` (audio TTS), latencias en ms y proveedores de cada etapa.
- `session_id: str | None`: identificador de sesión de audio en el storage neutro.
- `corr_id: str | None`: correlación compartida con la capa HTTP.
- `meta: dict[str, str] | None`: etiquetas de contexto (por ejemplo, `context: diario_emocional`).

El contrato no garantiza entrega inline de bytes (`tts_audio_bytes`); el campo canónico para la reproducción del TTS es `tts_url`.
