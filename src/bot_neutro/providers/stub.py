from .interfaces import LLMProvider, STTProvider, STTResult, TTSProvider, TTSResult


class StubSTTProvider(STTProvider):
    provider_id = "stub-stt"
    latency_ms = 100
    input_seconds = 1.0

    def transcribe(self, audio_bytes: bytes, locale: str) -> STTResult:  # pragma: no cover - simple stub
        return STTResult(text="stub transcript", raw_transcript={"locale": locale})


class StubLLMProvider(LLMProvider):
    provider_id = "stub-llm"
    latency_ms = 200

    def generate_reply(self, transcript: str, context: dict) -> str:  # pragma: no cover - simple stub
        return "stub reply text"


class StubTTSProvider(TTSProvider):
    provider_id = "stub-tts"
    latency_ms = 150
    output_seconds = 1.5
    audio_url = "https://example.com/audio/stub.wav"
    audio_mime_type = "audio/wav"

    def synthesize(self, text: str, locale: str, voice: str | None = None) -> TTSResult:  # pragma: no cover - simple stub
        return TTSResult(
            audio_bytes=b"stub-bytes",
            audio_mime_type=self.audio_mime_type,
            provider_id=self.provider_id,
            audio_url=self.audio_url,
        )


__all__ = ["StubSTTProvider", "StubTTSProvider", "StubLLMProvider"]
