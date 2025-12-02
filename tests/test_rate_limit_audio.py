import os

from fastapi.testclient import TestClient

from bot_neutro.api import create_app


def _restore_env(previous: dict) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_rate_limit_disabled_does_not_block_audio_requests():
    previous_env = {
        "RATE_LIMIT_ENABLED": os.environ.pop("RATE_LIMIT_ENABLED", None),
    }

    try:
        client = TestClient(create_app())

        for _ in range(3):
            response = client.post(
                "/audio",
                files={"file": ("test.wav", b"fake audio", "audio/wav")},
                headers={"X-API-Key": "rl-test"},
            )
            assert response.status_code != 429
    finally:
        _restore_env(previous_env)


def test_audio_rate_limit_blocks_after_threshold():
    previous_env = {
        "RATE_LIMIT_ENABLED": os.environ.get("RATE_LIMIT_ENABLED"),
        "RATE_LIMIT_AUDIO_WINDOW_SECONDS": os.environ.get(
            "RATE_LIMIT_AUDIO_WINDOW_SECONDS"
        ),
        "RATE_LIMIT_AUDIO_MAX_REQUESTS": os.environ.get("RATE_LIMIT_AUDIO_MAX_REQUESTS"),
    }

    try:
        os.environ["RATE_LIMIT_ENABLED"] = "1"
        os.environ["RATE_LIMIT_AUDIO_WINDOW_SECONDS"] = "60"
        os.environ["RATE_LIMIT_AUDIO_MAX_REQUESTS"] = "2"

        client = TestClient(create_app())

        for _ in range(2):
            response = client.post(
                "/audio",
                files={"file": ("test.wav", b"fake audio", "audio/wav")},
                headers={"X-API-Key": "rl-user-1"},
            )
            assert response.status_code != 429

        response = client.post(
            "/audio",
            files={"file": ("test.wav", b"fake audio", "audio/wav")},
            headers={"X-API-Key": "rl-user-1"},
        )

        assert response.status_code == 429
        assert response.json()["detail"] == "rate limit exceeded"
        assert response.headers.get("X-Outcome") == "error"
        assert response.headers.get("X-Outcome-Detail") == "rate_limit"
        assert response.headers.get("Retry-After") is not None
        int(response.headers["Retry-After"])  # validate parseable
    finally:
        _restore_env(previous_env)


def test_rate_limit_does_not_apply_to_healthz_even_when_enabled():
    previous_env = {"RATE_LIMIT_ENABLED": os.environ.get("RATE_LIMIT_ENABLED")}

    try:
        os.environ["RATE_LIMIT_ENABLED"] = "1"
        client = TestClient(create_app())

        for _ in range(100):
            response = client.get("/healthz")
            assert response.status_code != 429
    finally:
        _restore_env(previous_env)
