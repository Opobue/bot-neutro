import uuid
from datetime import datetime
from typing import Dict, Optional, Protocol, TypedDict, Union

from .audio_storage_inmemory import (
    AudioSession,
    DEFAULT_AUDIO_SESSION_REPOSITORY,
    InMemoryAudioSessionRepository,
)


class AudioRequestContext(TypedDict, total=False):
    corr_id: str
    api_key_id: str
    audio_bytes: bytes
    raw_audio: bytes
    mime_type: str
    language_hint: Optional[str]
    locale: Optional[str]
    user_external_id: Optional[str]
    client_meta: Optional[Dict[str, str]]
    client_metadata: Optional[Dict[str, str]]


class UsageMetrics(TypedDict):
    stt_ms: int
    llm_ms: int
    tts_ms: int
    total_ms: int
    provider_stt: str
    provider_llm: str
    provider_tts: str
    input_seconds: float
    output_seconds: float


class AudioResponseContext(TypedDict):
    transcript: str
    reply_text: str
    tts_url: Optional[str]
    usage: UsageMetrics
    session_id: Optional[str]
    corr_id: Optional[str]
    meta: Optional[Dict[str, str]]


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
        api_key_id = ctx.get("api_key_id")
        audio_bytes = ctx.get("audio_bytes") or ctx.get("raw_audio")
        mime_type = ctx.get("mime_type", "")
        client_metadata = ctx.get("client_meta") or ctx.get("client_metadata")

        if not api_key_id:
            return PipelineError(
                code="unauthorized", message="missing api key", details=None
            )

        if not audio_bytes:
            return PipelineError(code="bad_request", message="empty audio", details=None)

        if not mime_type.startswith("audio/"):
            return PipelineError(
                code="unsupported_media_type",
                message="unsupported media type",
                details={"mime_type": mime_type},
            )

        metadata = client_metadata
        munay_user_id: Optional[str] = None
        munay_context: Optional[str] = None

        if metadata:
            munay_user_id = metadata.get("munay_user_id")
            munay_context = metadata.get("munay_context")

        usage: UsageMetrics = {
            "stt_ms": 100,
            "llm_ms": 200,
            "tts_ms": 150,
            "total_ms": 450,
            "provider_stt": "stub-stt",
            "provider_llm": "stub-llm",
            "provider_tts": "stub-tts",
            "input_seconds": 1.0,
            "output_seconds": 1.5,
        }
        session_id = str(uuid.uuid4())

        session: AudioSession = {
            "id": session_id,
            "corr_id": ctx.get("corr_id", str(uuid.uuid4())),
            "api_key_id": api_key_id,
            "user_external_id": ctx.get("user_external_id") or munay_user_id,
            "created_at": datetime.utcnow(),
            "request_mime_type": mime_type,
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
            "meta_tags": {"context": munay_context} if munay_context else None,
        }

        self._repository.create(session)

        return AudioResponseContext(
            transcript=session["transcript"],
            reply_text=session["reply_text"],
            tts_url=session["tts_storage_ref"],
            usage=usage,
            session_id=session_id,
            corr_id=session["corr_id"],
            meta=session.get("meta_tags"),
        )


__all__ = [
    "AudioRequestContext",
    "AudioResponseContext",
    "UsageMetrics",
    "PipelineError",
    "AudioPipeline",
    "StubAudioPipeline",
]
