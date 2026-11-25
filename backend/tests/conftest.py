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


def _login_token(email: str, password: str) -> str:
    with TestClient(app) as c:
        res = c.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200
        return res.json()["access_token"]


@pytest.fixture
def admin_token():
    """Obtient un token d'accès administrateur unifié sans polluer les cookies de `client`."""
    return _login_token("admin@smartcampus.tn", "AdminSmartCampus2026!")


@pytest.fixture
def teacher_token():
    """Obtient un token d'accès enseignant (IIT) sans polluer les cookies de `client`."""
    return _login_token("enseignant.iit@smartcampus.tn", "TeacherPassword2026!")


@pytest.fixture
def candidate_token():
    """Obtient un token d'accès candidat sans polluer les cookies de `client`."""
    return _login_token("sarra.benali@gmail.com", "CandidatePassword2026!")
