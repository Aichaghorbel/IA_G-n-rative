from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_principal, get_db, require_roles
from app.core.exceptions import ResourceNotFoundException
from app.models.candidate import CandidateProfile
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationAdjustRequest,
    RecommendationRejectRequest,
    RecommendationResponse
)
from app.services.candidate_service import candidate_service
from app.services.recommendation_service import recommendation_service

router = APIRouter()


@router.get(
    "/me",
    response_model=List[RecommendationResponse],
    summary="Mes recommandations de parcours (Candidat)",
    description="Liste les recommandations de parcours du candidat connecté générées par le système agentique."
)
def get_my_recommendations(
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    if not profile:
        raise ResourceNotFoundException("profil candidat", principal.id)

    recs = db.query(Recommendation).filter(Recommendation.candidate_id == profile.id).all()
    if not recs:
        # Génération automatique si première consultation
        rec = recommendation_service.generate_recommendations(db, profile.id)
        recs = [rec]

    return [recommendation_service.build_recommendation_response(r) for r in recs]


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Détail d'une recommandation",
    description="Consulte le détail d'une recommandation (parcours, score de compatibilité, justification)."
)
def get_recommendation_detail(
    recommendation_id: int,
    principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)

    if principal.role in ["Enseignant", "enseignant", "E"]:
        candidate_service.verify_teacher_access(principal.id, rec.candidate)

    return recommendation_service.build_recommendation_response(rec)


@router.patch(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Ajuster ou valider une recommandation (E affecté ou Admin)",
    description="L'enseignant ou l'administrateur valide ou ajuste la recommandation académique."
)
def adjust_recommendation(
    recommendation_id: int,
    data: RecommendationAdjustRequest,
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)

    if principal.role in ["Enseignant", "enseignant", "E"]:
        candidate_service.verify_teacher_access(principal.id, rec.candidate)

    rec.formation_id = data.nouvelle_formation_id
    rec.justification = data.justification
    rec.status = "ajuste"
    rec.valide_par = principal.id
    db.commit()
    db.refresh(rec)
    return recommendation_service.build_recommendation_response(rec)


@router.post(
    "/{recommendation_id}/accept",
    summary="Accepter une recommandation (Candidat)",
    description="Le candidat accepte l'orientation recommandée, ce qui valide son choix de formation."
)
def accept_recommendation(
    recommendation_id: int,
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)

    rec.status = "valide"
    db.commit()
    return {"message": "Recommandation acceptée avec succès", "status": "valide"}


@router.post(
    "/{recommendation_id}/reject",
    summary="Refuser une recommandation (Candidat)",
    description="Le candidat rejette une recommandation avec un motif pour déclencher une nouvelle proposition."
)
def reject_recommendation(
    recommendation_id: int,
    data: RecommendationRejectRequest,
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)

    rec.status = "refuse"
    rec.motif_rejet = data.motif
    db.commit()
    return {"message": "Recommandation rejetée. Un nouvel ajustement d'orientation est planifié.", "status": "refuse"}
