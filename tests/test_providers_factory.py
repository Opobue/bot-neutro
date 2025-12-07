import pytest

from bot_neutro.providers import factory
from bot_neutro.providers.azure import AzureSTTProvider, AzureTTSProvider
from bot_neutro.providers.stub import StubLLMProvider, StubSTTProvider, StubTTSProvider


def test_build_stt_provider_defaults_to_stub(monkeypatch):
    monkeypatch.delenv("AUDIO_STT_PROVIDER", raising=False)
    provider = factory.build_stt_provider()
    assert isinstance(provider, StubSTTProvider)


def test_build_tts_provider_defaults_to_stub(monkeypatch):
    monkeypatch.delenv("AUDIO_TTS_PROVIDER", raising=False)
    provider = factory.build_tts_provider()
    assert isinstance(provider, StubTTSProvider)


def test_build_llm_provider_is_stub(monkeypatch):
    provider = factory.build_llm_provider()
    assert isinstance(provider, StubLLMProvider)


def test_build_stt_provider_azure_missing_config(monkeypatch):
    monkeypatch.setenv("AUDIO_STT_PROVIDER", "azure")
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)

    with pytest.raises(ValueError):
        factory.build_stt_provider()


def test_build_tts_provider_returns_azure_when_configured(monkeypatch):
    monkeypatch.setenv("AUDIO_TTS_PROVIDER", "azure")
    monkeypatch.setenv("AZURE_SPEECH_KEY", "dummy-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")
    monkeypatch.setenv("AZURE_SPEECH_STT_LANGUAGE_DEFAULT", "es-ES")
    monkeypatch.setenv("AZURE_SPEECH_TTS_VOICE_DEFAULT", "es-ES-AlonsoNeural")

    provider = factory.build_tts_provider()
    assert isinstance(provider, AzureTTSProvider)


def test_build_stt_provider_returns_azure_when_configured(monkeypatch):
    monkeypatch.setenv("AUDIO_STT_PROVIDER", "azure")
    monkeypatch.setenv("AZURE_SPEECH_KEY", "dummy-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")

    provider = factory.build_stt_provider()
    assert isinstance(provider, AzureSTTProvider)
