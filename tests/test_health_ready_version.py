from fastapi.testclient import TestClient

from bot_neutro import __version__
from bot_neutro.api import create_app

client = TestClient(create_app())


def test_healthz_default_headers_and_status():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("X-Outcome") == "ok"
    assert response.headers.get("X-Correlation-Id")


def test_readyz_default_headers_and_status():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("X-Outcome") == "ok"
    assert response.headers.get("X-Correlation-Id")


def test_version_returns_package_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": __version__}
    assert response.headers.get("X-Outcome") == "ok"


def test_correlation_id_propagation_when_provided():
    corr_id = "test-corr-id"
    response = client.get("/healthz", headers={"X-Correlation-Id": corr_id})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id") == corr_id
