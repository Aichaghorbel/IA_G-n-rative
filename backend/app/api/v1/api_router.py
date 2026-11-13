from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin,
    appointments,
    auth,
    candidates,
    conversations,
    documents,
    notifications,
    preregistrations,
    qcm,
    recommendations,
    stats
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentification & Comptes"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidats & Profils"])
api_router.include_router(preregistrations.router, prefix="/preregistrations", tags=["Préinscriptions"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations & IA Multimodale"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents & Corpus RAG"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommandations de Parcours"])
api_router.include_router(qcm.router, prefix="/qcm", tags=["QCM Adaptatif"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Rendez-vous & Entretiens"])
api_router.include_router(notifications.router, tags=["Notifications & Emails"])
api_router.include_router(stats.router, prefix="/stats", tags=["Statistiques & Décision"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administration & Supervision"])
