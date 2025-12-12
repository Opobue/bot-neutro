from dataclasses import dataclass
from typing import Optional


@dataclass
class STTResult:
    text: str
    provider_id: str
    raw_transcript: Optional[dict] = None


@dataclass
class TTSResult:
    audio_bytes: bytes
    audio_mime_type: str
    provider_id: str
    audio_url: Optional[str] = None


class STTProvider:
    provider_id: str = "stt"
    latency_ms: int = 0

    def transcribe(self, audio_bytes: bytes, locale: str) -> STTResult:
        raise NotImplementedError


class TTSProvider:
    provider_id: str = "tts"
    latency_ms: int = 0

    def synthesize(self, text: str, locale: str, voice: Optional[str] = None) -> TTSResult:
        raise NotImplementedError


class LLMProvider:
    provider_id: str = "llm"
    latency_ms: int = 0

    def generate_reply(self, transcript: str, context: dict) -> str:
        raise NotImplementedError
