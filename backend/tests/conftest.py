import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.core.database import Base, SessionLocal, engine
from scripts.seed_demo_data import seed_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initialise la base de données et insère les données de démo."""
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


@pytest.fixture
def client():
    """Client de test FastAPI."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    """Obtient un token d'accès administrateur unifié."""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@smartcampus.tn",
        "password": "AdminSmartCampus2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def teacher_token(client):
    """Obtient un token d'accès enseignant (IIT)."""
    res = client.post("/api/v1/auth/login", json={
        "email": "enseignant.iit@smartcampus.tn",
        "password": "TeacherPassword2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def candidate_token(client):
    """Obtient un token d'accès candidat."""
    res = client.post("/api/v1/auth/login", json={
        "email": "sarra.benali@gmail.com",
        "password": "CandidatePassword2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]
