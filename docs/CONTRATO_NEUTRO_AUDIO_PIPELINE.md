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
    tts_audio_bytes: bytes | None
    tts_audio_url: str | None
    usage: UsageMetrics
    session_id: str | None

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

Las respuestas exitosas deben devolver `200 OK` con `X-Outcome: ok`. `X-Outcome-Detail` **no se incluye** en respuestas 2xx por defecto y se reserva para errores (4xx/5xx). En errores, `X-Outcome` debe ser `error` y `X-Outcome-Detail` debe contener uno de los códigos de la tabla anterior.
