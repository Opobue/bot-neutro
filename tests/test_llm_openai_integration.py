import os

import pytest

from bot_neutro.providers.openai_llm import OpenAILLMProvider
from bot_neutro.providers.stub import StubLLMProvider

pytestmark = pytest.mark.llm_integration


def test_openai_llm_integration_basic_roundtrip():
    api_key = os.getenv("OPENAI_API_KEY")
    model_freemium = os.getenv("OPENAI_MODEL_FREEMIUM")
    enabled = os.getenv("OPENAI_LLM_TEST_ENABLED")

    if not api_key or not model_freemium or enabled != "1":
        pytest.skip("OpenAI LLM integration not enabled or not configured")

    provider = OpenAILLMProvider.from_env(fallback=StubLLMProvider())

    transcript = "Hola, este es un test corto de integración del LLM."
    context = {"llm_tier": "freemium"}

    reply = provider.generate_reply(transcript, context)

    assert isinstance(reply, str)
    assert reply.strip() != ""
    assert "openai-llm" in provider.provider_id
    assert provider.latency_ms >= 0
