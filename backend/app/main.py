import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import AppException
from app.core.security import get_password_hash
from app.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisation au démarrage : création des tables et utilisateur admin initial."""
    Base.metadata.create_all(bind=engine)

    # Initialisation de l'administrateur unifié par défaut
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "admin@smartcampus.tn").first()
        if not admin_user:
            admin_user = User(
                email="admin@smartcampus.tn",
                hashed_password=get_password_hash("AdminSmartCampus2026!"),
                role="Administrateur",
                nom="Administrateur",
                prenom="Plateforme",
                telephone="+216 74 000 000",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

    yield


# ==============================================================================
# Initialisation de l'application FastAPI
# ==============================================================================
app = FastAPI(
    title=f"{settings.APP_NAME} — API d'Orientation Universitaire",
    description="""
# 🎓 SmartCampus AI — Spécification & Documentation Technique des API

Bienvenue sur la documentation interactive des API de **SmartCampus AI**, plateforme agentique d'orientation universitaire pour les établissements **IIT** (Institut International de Technologie) et **ISB** (International School of Business) du réseau UNA Sfax.

---

### 🛡️ Les 4 Rôles du Système & Règles d'Accès (RBAC Casbin)
Chaque requête est filtrée selon le rôle du demandeur :
1. **Visiteur** : Session anonyme via `X-Session-Token` (sliding 30 jours). Chat interactif, découverte des filières, vérification OTP et préinscription.
2. **Candidat** : Authentifié par JWT (access 15 min + refresh 7 jours). Accède à son profil enrichi, passe son QCM, consulte ses recommandations et ses rendez-vous.
3. **Enseignant** : Responsable académique / d'entretien. Accède uniquement aux candidats qui lui sont explicitement affectés.
4. **Administrateur unifié** : Gestion globale et transverse (IIT et ISB simultanément) : enseignants, corpus RAG, supervision des agents IA et statistiques.

---

### 📡 En-têtes HTTP Standards
- `Authorization`: `Bearer <access_token>` (utilisateurs Candidat, Enseignant, Administrateur)
- `X-Session-Token`: `<session_token>` (utilisateurs Visiteur)
- `X-Request-Id`: `req_<uuid>` (traçabilité de bout en bout)
- `Accept-Language`: `fr` | `tn` | `arabizi`

---

### ⚠️ Gestion Standardisée des Erreurs (Format Officiel Section 5.1)
Toutes les erreurs 4xx et 5xx renvoient l'objet structuré :
```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Email ou mot de passe incorrect",
    "details": { "field": "email" },
    "timestamp": "2026-10-27T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# ==============================================================================
# Middlewares : CORS, Request-ID et Temps de Réponse
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "X-Response-Time", "X-Total-Count", "Link", "Retry-After"]
)


@app.middleware("http")
async def request_timing_and_id_middleware(request: Request, call_next):
    """Ajoute X-Request-Id et X-Response-Time aux en-têtes de réponse."""
    request_id = request.headers.get("X-Request-Id") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


# ==============================================================================
# Gestion Standardisée des Exceptions (Section 5.1, 5.4 et 5.5)
# ==============================================================================
def get_req_id(request: Request) -> str:
    return getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Gestion des erreurs métier SmartCampus AI."""
    payload = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details if exc.details else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": get_req_id(request)
        }
    }
    return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Gestion des erreurs 422 de validation Pydantic.
    Format conforme Section 5.5 : liste des champs avec problème.
    """
    details = []
    for err in exc.errors():
        field_loc = err.get("loc", [])
        field_name = ".".join(str(l) for l in field_loc if l != "body")
        details.append({
            "field": field_name or "body",
            "issue": err.get("msg", "valeur invalide"),
            "value": str(err.get("input", ""))[:100]
        })

    payload = {
        "error": {
            "code": "VALIDATION_FAILED",
            "message": "Données envoyées invalides ou incomplètes",
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": get_req_id(request)
        }
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Gestion des erreurs HTTP standard (404, 405, etc.)."""
    error_codes = {
        400: "BAD_REQUEST",
        401: "AUTH_002",
        403: "AUTH_003",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    code = error_codes.get(exc.status_code, f"HTTP_{exc.status_code}")
    payload = {
        "error": {
            "code": code,
            "message": str(exc.detail),
            "details": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": get_req_id(request)
        }
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Gestion des erreurs inattendues (500 Internal Server Error)."""
    payload = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Une erreur interne inattendue s'est produite sur le serveur.",
            "details": {"error_type": type(exc).__name__, "description": str(exc)} if settings.DEBUG else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": get_req_id(request)
        }
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)


# ==============================================================================
# Inclusion des routes de l'API v1
# ==============================================================================
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Santé du Système"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "redoc": "/redoc",
        "api_v1": settings.API_V1_STR
    }


@app.get("/health", tags=["Santé du Système"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "version": "1.0.0"
    }
