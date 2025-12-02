import uuid
from typing import Dict, Optional, Protocol, TypedDict, Union


class AudioRequestContext(TypedDict):
    corr_id: str
    api_key_id: str
    raw_audio: bytes
    mime_type: str
    language_hint: Optional[str]
    client_metadata: Optional[Dict[str, str]]


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
    tts_audio_bytes: Optional[bytes]
    tts_audio_url: Optional[str]
    usage: UsageMetrics
    session_id: Optional[str]


class PipelineError(TypedDict):
    code: str
    message: str
    details: Optional[Dict[str, str]]


class AudioPipeline(Protocol):
    def process(self, ctx: AudioRequestContext) -> Union[AudioResponseContext, PipelineError]:
        ...


class StubAudioPipeline:
    def process(self, ctx: AudioRequestContext) -> Union[AudioResponseContext, PipelineError]:
        if not ctx["api_key_id"]:
            return PipelineError(
                code="unauthorized", message="missing api key", details=None
            )

        if not ctx["raw_audio"]:
            return PipelineError(code="bad_request", message="empty audio", details=None)

        if not ctx["mime_type"].startswith("audio/"):
            return PipelineError(
                code="unsupported_media_type",
                message="unsupported media type",
                details={"mime_type": ctx["mime_type"]},
            )

        usage: UsageMetrics = {
            "stt_ms": 100,
            "llm_ms": 200,
            "tts_ms": 150,
            "total_ms": 450,
            "provider_stt": "stub-stt",
            "provider_llm": "stub-llm",
            "provider_tts": "stub-tts",
        }
        session_id = str(uuid.uuid4())

        return AudioResponseContext(
            transcript="stub transcript",
            reply_text="stub reply text",
            tts_audio_bytes=None,
            tts_audio_url="https://example.com/audio/stub.wav",
            usage=usage,
            session_id=session_id,
        )


__all__ = [
    "AudioRequestContext",
    "AudioResponseContext",
    "UsageMetrics",
    "PipelineError",
    "AudioPipeline",
    "StubAudioPipeline",
]
