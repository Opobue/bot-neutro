from typing import Any, Dict

from .interfaces import LLMProvider, STTProvider, STTResult, TTSProvider, TTSResult


class StubSTTProvider(STTProvider):
    provider_id = "stub-stt"
    latency_ms = 100
    input_seconds = 1.0

    # pragma: no cover - simple stub
    def transcribe(self, audio_bytes: bytes, locale: str) -> STTResult:
        return STTResult(
            text="stub transcript",
            provider_id=self.provider_id,
            raw_transcript={"locale": locale},
        )


class StubLLMProvider(LLMProvider):
    provider_id = "stub-llm"
    latency_ms = 200

    # pragma: no cover - simple stub
    def generate_reply(self, transcript: str, context: Dict[str, Any]) -> str:
        return "stub reply text"


class StubTTSProvider(TTSProvider):
    provider_id = "stub-tts"
    latency_ms = 150
    output_seconds = 1.5
    audio_url = "https://example.com/audio/stub.wav"
    audio_mime_type = "audio/wav"

    # pragma: no cover - simple stub
    def synthesize(
        self, text: str, locale: str, voice: str | None = None
    ) -> TTSResult:
        return TTSResult(
            audio_bytes=b"stub-bytes",
            audio_mime_type=self.audio_mime_type,
            provider_id=self.provider_id,
            audio_url=self.audio_url,
        )


__all__ = ["StubSTTProvider", "StubTTSProvider", "StubLLMProvider"]
