import os

from .azure import AzureSTTProvider, AzureTTSProvider
from .interfaces import LLMProvider, STTProvider, TTSProvider
from .stub import StubLLMProvider, StubSTTProvider, StubTTSProvider


def build_stt_provider() -> STTProvider:
    provider_name = os.getenv("AUDIO_STT_PROVIDER", "stub").lower()
    if provider_name == "azure":
        return AzureSTTProvider.from_env()
    return StubSTTProvider()


def build_tts_provider() -> TTSProvider:
    provider_name = os.getenv("AUDIO_TTS_PROVIDER", "stub").lower()
    if provider_name == "azure":
        return AzureTTSProvider.from_env()
    return StubTTSProvider()


def build_llm_provider() -> LLMProvider:
    return StubLLMProvider()


__all__ = ["build_stt_provider", "build_tts_provider", "build_llm_provider"]
