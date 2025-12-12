import os

import pytest

from bot_neutro.providers.azure import AzureSTTProvider
from bot_neutro.providers.stub import StubSTTProvider


pytestmark = pytest.mark.azure_integration


def test_azure_stt_returns_real_transcript_or_skips_when_unconfigured():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    wav_path = os.getenv("AZURE_SPEECH_TEST_WAV_PATH")

    if not (speech_key and speech_region and wav_path):
        pytest.skip("Azure integration test skipped: missing env")

    with open(wav_path, "rb") as wav_file:
        audio_bytes = wav_file.read()

    provider = AzureSTTProvider.from_env(fallback=StubSTTProvider())
    locale = os.getenv("AZURE_SPEECH_STT_LANGUAGE_DEFAULT", "es-ES")

    result = provider._transcribe_with_sdk(audio_bytes, locale)  # noqa: SLF001

    assert result.text
    assert result.text != "stub transcript"
    assert "stub-stt" not in result.provider_id
