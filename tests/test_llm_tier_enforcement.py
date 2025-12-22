from fastapi.testclient import TestClient

from bot_neutro.api import create_app
from bot_neutro.metrics_runtime import METRICS
from bot_neutro.security_ids import derive_api_key_id


client = TestClient(create_app())


def _get_llm_tier_denied_count(snapshot, requested_tier, authorized_tier):
    for item in snapshot.get("llm_tier_denied_total", []):
        if (
            item.get("route") == "/audio"
            and item.get("requested_tier") == requested_tier
            and item.get("authorized_tier") == authorized_tier
        ):
            return item.get("value", 0)
    return 0


def test_audio_without_tier_header_uses_authorized_tier(monkeypatch):
    monkeypatch.setenv(
        "MUNAY_LLM_PREMIUM_API_KEY_IDS",
        derive_api_key_id("premium-key"),
    )

    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={"X-API-Key": "premium-key"},
    )

    assert response.status_code == 200
    assert response.headers.get("X-Outcome") == "success"


def test_audio_allows_requested_tier_below_authorized(monkeypatch):
    monkeypatch.setenv(
        "MUNAY_LLM_PREMIUM_API_KEY_IDS",
        derive_api_key_id("premium-key"),
    )

    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={
            "X-API-Key": "premium-key",
            "x-munay-llm-tier": "freemium",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("X-Outcome") == "success"


def test_audio_rejects_requested_tier_above_authorized(monkeypatch):
    monkeypatch.setenv(
        "MUNAY_LLM_PREMIUM_API_KEY_IDS",
        derive_api_key_id("premium-key"),
    )

    snapshot_before = METRICS.snapshot()
    denied_before = _get_llm_tier_denied_count(snapshot_before, "premium", "freemium")
    errors_before = snapshot_before["errors_total"].get("/audio", 0)

    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={
            "X-API-Key": "free-key",
            "x-munay-llm-tier": "premium",
        },
    )

    assert response.status_code == 403
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "llm.tier_forbidden"
    assert response.headers.get("X-Correlation-Id")
    assert response.json().get("detail") == "llm.tier_forbidden"

    snapshot_after = METRICS.snapshot()
    denied_after = _get_llm_tier_denied_count(snapshot_after, "premium", "freemium")
    errors_after = snapshot_after["errors_total"].get("/audio", 0)

    assert denied_after == denied_before + 1
    assert errors_after == errors_before + 1


def test_audio_rejects_invalid_tier_header(monkeypatch):
    monkeypatch.setenv(
        "MUNAY_LLM_PREMIUM_API_KEY_IDS",
        derive_api_key_id("premium-key"),
    )

    snapshot_before = METRICS.snapshot()
    denied_before = _get_llm_tier_denied_count(snapshot_before, "gold", "freemium")
    errors_before = snapshot_before["errors_total"].get("/audio", 0)

    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
        headers={
            "X-API-Key": "free-key",
            "x-munay-llm-tier": "gold",
        },
    )

    assert response.status_code == 400
    assert response.headers.get("X-Outcome") == "error"
    assert response.headers.get("X-Outcome-Detail") == "llm.tier_invalid"
    assert response.headers.get("X-Correlation-Id")
    assert response.json().get("detail") == "llm.tier_invalid"

    snapshot_after = METRICS.snapshot()
    denied_after = _get_llm_tier_denied_count(snapshot_after, "gold", "freemium")
    errors_after = snapshot_after["errors_total"].get("/audio", 0)

    assert denied_after == denied_before
    assert errors_after == errors_before + 1
