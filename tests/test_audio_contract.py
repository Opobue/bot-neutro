from fastapi.testclient import TestClient

from bot_neutro.api import create_app


client = TestClient(create_app())


def test_audio_happy_path_returns_contract_fields_and_headers():
    response = client.post(
        "/audio",
        files={"file": ("test.wav", b"fake audio", "audio/wav")},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "transcript" in payload
    assert "reply_text" in payload
    assert "audio_url" in payload
    assert "usage" in payload
    assert "session_id" in payload

    usage = payload["usage"]
    for key in [
        "stt_ms",
        "llm_ms",
        "tts_ms",
        "total_ms",
        "provider_stt",
        "provider_llm",
        "provider_tts",
    ]:
        assert key in usage

    assert response.headers.get("X-Outcome") == "ok"
    assert response.headers.get("X-Correlation-Id")
    assert "X-Outcome-Detail" not in response.headers


def test_audio_without_api_key_returns_unauthorized():
    response = client.post(
        "/audio",
        files={"file": ("test.wav", b"fake audio", "audio/wav")},
    )

    assert response.status_code == 401
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "auth.unauthorized"
    assert response.headers.get("X-Correlation-Id")
    assert "detail" in response.json()


def test_audio_with_invalid_mime_type_returns_unsupported_media_type():
    response = client.post(
        "/audio",
        files={"file": ("test.txt", b"text content", "text/plain")},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 415
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "audio.unsupported_media_type"
    assert response.headers.get("X-Correlation-Id")
    assert "detail" in response.json()


def test_audio_with_empty_file_returns_bad_request():
    response = client.post(
        "/audio",
        files={"file": ("test.wav", b"", "audio/wav")},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 400
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "audio.bad_request"
    assert response.headers.get("X-Correlation-Id")
    assert "detail" in response.json()
