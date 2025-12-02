import uuid
from datetime import datetime
from typing import Dict, Optional, Protocol, TypedDict, Union

from .audio_storage_inmemory import (
    AudioSession,
    DEFAULT_AUDIO_SESSION_REPOSITORY,
    InMemoryAudioSessionRepository,
)


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
    def __init__(self, repository: InMemoryAudioSessionRepository | None = None) -> None:
        self._repository = repository or DEFAULT_AUDIO_SESSION_REPOSITORY

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

        session: AudioSession = {
            "id": session_id,
            "corr_id": ctx["corr_id"],
            "api_key_id": ctx["api_key_id"],
            "user_external_id": None,
            "created_at": datetime.utcnow(),
            "request_mime_type": ctx["mime_type"],
            "request_duration_seconds": None,
            "transcript": "stub transcript",
            "reply_text": "stub reply text",
            "tts_available": True,
            "tts_storage_ref": "https://example.com/audio/stub.wav",
            "usage_stt_ms": usage["stt_ms"],
            "usage_llm_ms": usage["llm_ms"],
            "usage_tts_ms": usage["tts_ms"],
            "usage_total_ms": usage["total_ms"],
            "provider_stt": usage["provider_stt"],
            "provider_llm": usage["provider_llm"],
            "provider_tts": usage["provider_tts"],
            "meta_tags": None,
        }

        self._repository.create(session)

        return AudioResponseContext(
            transcript=session["transcript"],
            reply_text=session["reply_text"],
            tts_audio_bytes=None,
            tts_audio_url=session["tts_storage_ref"],
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
