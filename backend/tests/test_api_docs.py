def test_swagger_ui_available(client):
    """Vérifie que la documentation Swagger UI est accessible sur /docs."""
    res = client.get("/docs")
    assert res.status_code == 200
    assert "swagger-ui" in res.text.lower()


def test_redoc_available(client):
    """Vérifie que la documentation ReDoc est accessible sur /redoc."""
    res = client.get("/redoc")
    assert res.status_code == 200
    assert "redoc" in res.text.lower()


def test_openapi_json_schema(client):
    """Vérifie le schéma OpenAPI JSON officiel."""
    res = client.get("/api/v1/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "SmartCampus AI" in schema["info"]["title"]
    assert "paths" in schema
    # Vérifie la présence des routes clés
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/candidates" in schema["paths"]
    assert "/api/v1/conversations" in schema["paths"]
    assert "/api/v1/documents" in schema["paths"]
    assert "/api/v1/qcm" in schema["paths"]
    assert "/api/v1/appointments" in schema["paths"]
