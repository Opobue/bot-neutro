import uuid
from datetime import datetime
from typing import Dict, Optional, TypedDict, Union

from .audio_storage_inmemory import (
    AudioSession,
    DEFAULT_AUDIO_SESSION_REPOSITORY,
    InMemoryAudioSessionRepository,
)
from .providers.interfaces import (
    LLMProvider,
    STTProvider,
    STTResult,
    TTSProvider,
    TTSResult,
)
from .providers.stub import StubLLMProvider, StubSTTProvider, StubTTSProvider


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


class AudioPipeline:
    def __init__(
        self,
        session_repo: InMemoryAudioSessionRepository,
        stt_provider: STTProvider,
        tts_provider: TTSProvider,
        llm_provider: LLMProvider,
    ) -> None:
        self._repository = session_repo
        self._stt_provider = stt_provider
        self._tts_provider = tts_provider
        self._llm_provider = llm_provider

    def _error(self, code: str, message: str, details: Optional[Dict[str, str]] = None) -> PipelineError:
        return PipelineError(code=code, message=message, details=details)

    def _build_usage(
        self,
        stt_result: STTResult,
        tts_result: TTSResult,
    ) -> UsageMetrics:
        stt_ms = int(getattr(self._stt_provider, "latency_ms", 0))
        llm_ms = int(getattr(self._llm_provider, "latency_ms", 0))
        tts_ms = int(getattr(self._tts_provider, "latency_ms", 0))

        input_seconds = float(getattr(self._stt_provider, "input_seconds", 0.0))
        output_seconds = float(getattr(self._tts_provider, "output_seconds", 0.0))

        provider_stt = getattr(stt_result, "provider_id", getattr(self._stt_provider, "provider_id", "stt"))
        provider_llm = getattr(self._llm_provider, "provider_id", "llm")
        provider_tts = getattr(tts_result, "provider_id", getattr(self._tts_provider, "provider_id", "tts"))

        total_ms = stt_ms + llm_ms + tts_ms

        return UsageMetrics(
            stt_ms=stt_ms,
            llm_ms=llm_ms,
            tts_ms=tts_ms,
            total_ms=total_ms,
            provider_stt=provider_stt,
            provider_llm=provider_llm,
            provider_tts=provider_tts,
            input_seconds=input_seconds,
            output_seconds=output_seconds,
        )

    def process(self, ctx: AudioRequestContext) -> Union[AudioResponseContext, PipelineError]:
        api_key_id = ctx.get("api_key_id")
        audio_bytes = ctx.get("audio_bytes") or ctx.get("raw_audio")
        mime_type = ctx.get("mime_type", "")
        client_metadata = ctx.get("client_meta") or ctx.get("client_metadata")
        locale = ctx.get("locale") or ctx.get("language_hint") or ""

        if not api_key_id:
            return self._error(code="unauthorized", message="missing api key")

        if not audio_bytes:
            return self._error(code="bad_request", message="empty audio")

        if not mime_type.startswith("audio/"):
            return self._error(
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

        corr_id = ctx.get("corr_id", str(uuid.uuid4()))

        try:
            stt_result = self._stt_provider.transcribe(audio_bytes, locale)
        except TimeoutError as exc:  # pragma: no cover - defensive branch
            return self._error(code="provider_timeout", message=str(exc))
        except Exception as exc:  # pragma: no cover - defensive branch
            return self._error(code="stt_error", message=str(exc))

        try:
            reply_text = self._llm_provider.generate_reply(
                stt_result.text,
                {
                    "metadata": metadata or {},
                    "user_external_id": ctx.get("user_external_id") or munay_user_id,
                },
            )
        except TimeoutError as exc:  # pragma: no cover - defensive branch
            return self._error(code="provider_timeout", message=str(exc))
        except Exception as exc:  # pragma: no cover - defensive branch
            return self._error(code="llm_error", message=str(exc))

        try:
            tts_result = self._tts_provider.synthesize(reply_text, locale, voice=None)
        except TimeoutError as exc:  # pragma: no cover - defensive branch
            return self._error(code="provider_timeout", message=str(exc))
        except Exception as exc:  # pragma: no cover - defensive branch
            return self._error(code="tts_error", message=str(exc))

        usage = self._build_usage(stt_result, tts_result)
        session_id = str(uuid.uuid4())

        tts_url = getattr(tts_result, "audio_url", None)

        session: AudioSession = {
            "id": session_id,
            "corr_id": corr_id,
            "api_key_id": api_key_id,
            "user_external_id": ctx.get("user_external_id") or munay_user_id,
            "created_at": datetime.utcnow(),
            "request_mime_type": mime_type,
            "request_duration_seconds": None,
            "transcript": stt_result.text,
            "reply_text": reply_text,
            "tts_available": bool(tts_result.audio_bytes),
            "tts_storage_ref": tts_url,
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


class StubAudioPipeline(AudioPipeline):
    def __init__(self, repository: InMemoryAudioSessionRepository | None = None) -> None:
        super().__init__(
            repository or DEFAULT_AUDIO_SESSION_REPOSITORY,
            StubSTTProvider(),
            StubTTSProvider(),
            StubLLMProvider(),
        )


__all__ = [
    "AudioRequestContext",
    "AudioResponseContext",
    "UsageMetrics",
    "PipelineError",
    "AudioPipeline",
    "StubAudioPipeline",
]
