from dataclasses import dataclass
from typing import Optional


@dataclass
class STTResult:
    text: str
    raw_transcript: Optional[dict] = None


@dataclass
class TTSResult:
    audio_bytes: bytes
    audio_mime_type: str
    provider_id: str
    audio_url: Optional[str] = None


class STTProvider:
    def transcribe(self, audio_bytes: bytes, locale: str) -> STTResult:
        raise NotImplementedError


class TTSProvider:
    def synthesize(self, text: str, locale: str, voice: Optional[str] = None) -> TTSResult:
        raise NotImplementedError


class LLMProvider:
    def generate_reply(self, transcript: str, context: dict) -> str:
        raise NotImplementedError
