from fastapi.testclient import TestClient

from bot_neutro.api import create_app

client = TestClient(create_app())


def test_success_responses_do_not_include_outcome_detail():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.headers.get("X-Outcome") == "ok"
    assert "X-Outcome-Detail" not in response.headers


def test_error_responses_include_outcome_detail():
    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
    )

    assert response.status_code == 401
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "auth.unauthorized"
