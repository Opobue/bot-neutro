"""Providers Azure Speech skeleton.

Estos providers son el punto de integración con Azure Speech SDK en órdenes
futuras. No almacenan claves ni tokens; leen configuración solo desde
variables de entorno y usan atributos simples para exponer metadatos de
proveedor. Las llamadas de red reales se implementarán en una iteración L3.
"""

import os
from dataclasses import dataclass

from .interfaces import LLMProvider, STTProvider, STTResult, TTSProvider, TTSResult


@dataclass
class AzureSpeechConfig:
    key: str
    region: str
    stt_language_default: str
    tts_voice_default: str


class AzureSTTProvider(STTProvider):
    provider_id = "azure-stt"
    latency_ms = 0
    input_seconds = 0.0

    def __init__(self, config: AzureSpeechConfig) -> None:
        self._config = config

    @classmethod
    def from_env(cls) -> "AzureSTTProvider":
        key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION")
        language_default = os.getenv("AZURE_SPEECH_STT_LANGUAGE_DEFAULT", "es-ES")
        voice_default = os.getenv("AZURE_SPEECH_TTS_VOICE_DEFAULT", "")

        if not key or not region:
            raise ValueError("Missing Azure Speech credentials: AZURE_SPEECH_KEY/AZURE_SPEECH_REGION")

        return cls(
            AzureSpeechConfig(
                key=key,
                region=region,
                stt_language_default=language_default,
                tts_voice_default=voice_default,
            )
        )

    def transcribe(self, audio_bytes: bytes, locale: str) -> STTResult:  # pragma: no cover - placeholder implementation
        raise NotImplementedError("Azure STT integration pending")


class AzureTTSProvider(TTSProvider):
    provider_id = "azure-tts"
    latency_ms = 0
    output_seconds = 0.0

    def __init__(self, config: AzureSpeechConfig) -> None:
        self._config = config

    @classmethod
    def from_env(cls) -> "AzureTTSProvider":
        key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION")
        language_default = os.getenv("AZURE_SPEECH_STT_LANGUAGE_DEFAULT", "es-ES")
        voice_default = os.getenv("AZURE_SPEECH_TTS_VOICE_DEFAULT", "es-ES-AlonsoNeural")

        if not key or not region:
            raise ValueError("Missing Azure Speech credentials: AZURE_SPEECH_KEY/AZURE_SPEECH_REGION")

        return cls(
            AzureSpeechConfig(
                key=key,
                region=region,
                stt_language_default=language_default,
                tts_voice_default=voice_default,
            )
        )

    def synthesize(self, text: str, locale: str, voice: str | None = None) -> TTSResult:  # pragma: no cover - placeholder implementation
        raise NotImplementedError("Azure TTS integration pending")


class AzureLLMProvider(LLMProvider):  # pragma: no cover - placeholder
    provider_id = "azure-llm"
    latency_ms = 0

    def generate_reply(self, transcript: str, context: dict) -> str:
        raise NotImplementedError("Azure LLM integration pending")


__all__ = ["AzureSTTProvider", "AzureTTSProvider", "AzureLLMProvider", "AzureSpeechConfig"]
