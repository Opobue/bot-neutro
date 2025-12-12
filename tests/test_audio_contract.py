from fastapi.testclient import TestClient

from bot_neutro.api import audio_session_repo, create_app


client = TestClient(create_app())


def test_audio_happy_path_returns_contract_fields_and_headers():
    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        data={"locale": "es-CO", "user_external_id": "test-user"},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "transcript" in payload
    assert "reply_text" in payload
    assert "tts_url" in payload
    assert "usage" in payload
    assert "session_id" in payload
    assert payload.get("corr_id")
    assert payload.get("meta") is None or isinstance(payload.get("meta"), dict)

    usage = payload["usage"]
    for key in [
        "input_seconds",
        "output_seconds",
        "stt_ms",
        "llm_ms",
        "tts_ms",
        "total_ms",
        "provider_stt",
        "provider_llm",
        "provider_tts",
    ]:
        assert key in usage

    assert response.headers.get("X-Outcome") == "success"
    assert response.headers.get("X-Outcome-Detail") == "audio_processed"
    assert response.headers.get("X-Correlation-Id")


def test_audio_allows_setting_premium_tier_via_header():
    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={
            "X-API-Key": "test-key",
            "X-Correlation-Id": "test-corr-id",
            "x-munay-llm-tier": "Premium",
        },
        data={"user_external_id": "test-user"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply_text"] == "stub reply text"


def test_audio_without_api_key_returns_unauthorized():
    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
    )

    assert response.status_code == 401
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "auth.unauthorized"
    assert response.headers.get("X-Correlation-Id")
    assert "detail" in response.json()


def test_audio_with_invalid_mime_type_returns_unsupported_media_type():
    response = client.post(
        "/audio",
        files={"audio_file": ("test.txt", b"text content", "text/plain")},
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
        files={"audio_file": ("test.wav", b"", "audio/wav")},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 400
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "audio.bad_request"
    assert response.headers.get("X-Correlation-Id")
    assert "detail" in response.json()


def test_audio_happy_path_creates_audio_session_in_repository():
    repo = audio_session_repo
    repo.clear()

    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={"X-API-Key": "test-key", "X-Correlation-Id": "test-corr-id"},
        data={"user_external_id": "test-user"},
    )

    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]

    sessions = repo.list_by_api_key("test-key", limit=10, offset=0)
    assert len(sessions) == 1

    session = sessions[0]
    assert session["id"] == session_id
    assert session["api_key_id"] == "test-key"
    assert session["corr_id"] == "test-corr-id"
    assert session["transcript"] == "stub transcript"
    assert session["reply_text"] == "stub reply text"
    assert session["tts_available"] is True
    assert session["tts_storage_ref"] == "https://example.com/audio/stub.wav"

    assert session["usage_stt_ms"] == data["usage"]["stt_ms"]
    assert session["usage_llm_ms"] == data["usage"]["llm_ms"]
    assert session["usage_tts_ms"] == data["usage"]["tts_ms"]
    assert session["usage_total_ms"] == data["usage"]["total_ms"]
    assert session["provider_stt"] == data["usage"]["provider_stt"]
    assert session["provider_llm"] == data["usage"]["provider_llm"]
    assert session["provider_tts"] == data["usage"]["provider_tts"]


def test_audio_with_munay_headers_populates_user_and_context_in_session():
    repo = audio_session_repo
    repo.clear()

    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={
            "X-API-Key": "test-key",
            "X-Correlation-Id": "corr-123",
            "x-munay-user-id": "user-123",
            "x-munay-context": "diario_emocional",
        },
    )

    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]

    sessions = repo.list_by_api_key("test-key", limit=10, offset=0)
    assert len(sessions) == 1

    session = sessions[0]
    assert session["id"] == session_id
    assert session["user_external_id"] == "user-123"
    assert session["corr_id"] == "corr-123"

    assert session["meta_tags"] is not None
    assert session["meta_tags"].get("context") == "diario_emocional"


def test_audio_with_invalid_munay_context_returns_bad_request():
    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={
            "X-API-Key": "test-key",
            "x-munay-user-id": "user-123",
            "x-munay-context": "invalid_context",
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "invalid x-munay-context"

    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "audio.bad_request"
    assert response.headers.get("X-Correlation-Id")
