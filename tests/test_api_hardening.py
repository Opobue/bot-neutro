
import os
from unittest import mock
import importlib
import pytest
from fastapi.testclient import TestClient

# We'll reload api to test env var changes for CORS
from bot_neutro import api

def test_exception_handler_headers():
    """
    Verifica que una excepción no manejada (500) devuelva:
    - X-Outcome: error
    - X-Outcome-Detail: internal_error
    - X-Correlation-Id: presente
    """
    # 1. Obtenemos la app (singleton o factory, en este caso get_app usa singleton _APP)
    #    Para no ensuciar el _APP global con rutas de test, idealmente limpiamos o usamos yield.
    #    Dado que api.py usa un singleton _APP, lo reseteamos para tener una app limpia si se necesita,
    #    o simplemente agregamos la ruta y luego la podríamos quitar (complejo).
    #    Simplemente agregamos ruta, el impacto es bajo para tests efímeros.
    
    app = api.get_app()
    
    # 2. Ruta dinámica que falla
    @app.get("/_test_500")
    def fail_endpoint():
        raise RuntimeError("Oops, catastrophic failure")

    client = TestClient(app)
    
    # 3. Request
    cid_input = "test-correlation-123"
    response = client.get("/_test_500", headers={"X-Correlation-Id": cid_input})
    
    # 4. Asserts
    assert response.status_code == 500
    assert response.headers["X-Outcome"] == "error"
    assert response.headers["X-Outcome-Detail"] == "internal_error"
    assert response.headers["X-Correlation-Id"] == cid_input
    
    # Validar body JSON estándar
    assert response.json() == {"detail": "Internal Server Error"}


def test_cors_configurable():
    """
    Verifica que MUNAY_CORS_ORIGINS controle la allowlist.
    Usamos reload(api) para simular el arranque con nuevas env vars.
    """
    new_origin = "https://staging.example.com"
    
    # Mockear env vars
    with mock.patch.dict(os.environ, {"MUNAY_CORS_ORIGINS": f"{new_origin}, http://localhost:9999"}):
        # Forzar recarga del módulo para que _parse_cors_origins y el middleware se reconstruyan
        importlib.reload(api)
        
        # Necesitamos forzar recreación de la app porque api._APP es global
        api._APP = None 
        app = api.get_app()
        client = TestClient(app)
        
        # 1. Origin Permitido
        resp_allowed = client.get(
            "/healthz", 
            headers={"Origin": new_origin, "Access-Control-Request-Method": "GET"}
        )
        # CORS headers deben estar presentes si el origin es aceptado
        assert resp_allowed.headers.get("access-control-allow-origin") == new_origin
        
        # 2. Origin NO permitido
        resp_blocked = client.get(
            "/healthz", 
            headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "GET"}
        )
        # CORS headers NO deben estar presentes
        assert "access-control-allow-origin" not in resp_blocked.headers

    # Teardown implícito: al salir del context manager, env vuelve. 
    # Pero el módulo api queda "sucio" con la config del mock.
    # Lo recargamos una vez más sin el mock para dejarlo "default" (localhost).
    importlib.reload(api)
    api._APP = None

