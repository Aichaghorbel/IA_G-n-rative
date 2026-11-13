def test_anonymous_session_creation(client):
    """Test création session anonyme visiteur."""
    res = client.post("/api/v1/auth/sessions/anonymous")
    assert res.status_code == 201
    data = res.json()
    assert "session_id" in data
    assert "session_token" in data
    assert data["role"] == "Visiteur"


def test_login_success(client):
    """Test connexion réussie avec identifiants valides."""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@smartcampus.tn",
        "password": "AdminSmartCampus2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "Administrateur"


def test_login_invalid_credentials(client):
    """Test échec de connexion (mauvais mot de passe) renvoie format d'erreur conforme."""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@smartcampus.tn",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
    assert "request_id" in data["error"]


def test_otp_flow(client):
    """Test flux complet OTP : demande puis vérification."""
    # 1. Demande OTP
    res_req = client.post("/api/v1/auth/otp/request", json={"email": "visiteur.test@gmail.com"})
    assert res_req.status_code == 200
    otp_code = res_req.json().get("dev_code")
    assert otp_code is not None

    # 2. Vérification OTP
    res_verif = client.post("/api/v1/auth/otp/verify", json={
        "email": "visiteur.test@gmail.com",
        "otp_code": otp_code
    })
    assert res_verif.status_code == 200
    assert res_verif.json()["verified"] is True


def test_me_endpoint_with_auth(client, admin_token):
    """Test consultation /me avec token JWT."""
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@smartcampus.tn"
    assert data["role"] == "Administrateur"
