def test_standard_error_format_on_not_found(client, admin_token):
    """Vérifie que l'erreur 404 renvoie exactement le format standard Section 5.1."""
    res = client.get(
        "/api/v1/candidates/99999",
        headers={"Authorization": f"Bearer {admin_token}", "X-Request-Id": "req_test_404"}
    )
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    err = data["error"]
    assert "code" in err
    assert "message" in err
    assert "timestamp" in err
    assert err["request_id"] == "req_test_404"


def test_validation_error_format_422(client):
    """Vérifie que les erreurs de validation Pydantic (422) sont formatées selon la Section 5.5."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "invalid-email-format", "password": "123"}
    )
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    err = data["error"]
    assert err["code"] == "VALIDATION_FAILED"
    assert isinstance(err["details"], list)
    assert any(d["field"] == "email" for d in err["details"])


def test_forbidden_role_access_403(client, candidate_token):
    """Vérifie qu'un candidat tentant d'accéder aux logs admin reçoit une 403 avec code AUTH_003."""
    res = client.get(
        "/api/v1/admin/logs",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert res.status_code == 403
    data = res.json()
    assert data["error"]["code"] == "AUTH_003"


def test_missing_rgpd_consent_422(client):
    """Vérifie que l'absence de consentement RGPD lève l'erreur CANDIDATE_002 (422)."""
    res = client.post(
        "/api/v1/preregistrations",
        json={
            "formation_id": 1,
            "consent_rgpd": False,
            "nom": "Test",
            "prenom": "User",
            "email": "test@rgpd.tn"
        }
    )
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "CANDIDATE_002"
