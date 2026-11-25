"""
Endpoints API pour les Recommandations d'orientation.
Strictement conformes au diagramme de classes UML.
Recommandation liée uniquement au Candidat (pas de formation_id).
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_principal, get_db, require_roles
from app.api.ownership import assert_can_access_candidat
from app.core.exceptions import ResourceNotFoundException
from app.models.candidate import CandidateProfile
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommandationCreate,
    RecommandationUpdate,
    RecommandationResponse
)
from app.services.recommendation_service import recommendation_service

router = APIRouter()


@router.get(
    "/me",
    response_model=List[RecommandationResponse],
    summary="Mes recommandations d'orientation (Candidat)",
    description="Liste les recommandations d'orientation du candidat connecté générées par le système agentique."
)
def get_my_recommendations(
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    if not profile:
        raise ResourceNotFoundException("profil candidat", principal.id)

    recs = db.query(Recommendation).filter(Recommendation.candidat_id == profile.id).all()
    if not recs:
        # Génération automatique si première consultation
        rec = recommendation_service.generate_recommendations(db, profile.id)
        recs = [rec]

    return [recommendation_service.build_recommendation_response(r) for r in recs]


@router.get(
    "/{recommendation_id}",
    response_model=RecommandationResponse,
    summary="Détail d'une recommandation",
    description="Consulte le détail d'une recommandation (score de compatibilité, justification)."
)
def get_recommendation_detail(
    recommendation_id: int,
    principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)
    assert_can_access_candidat(db, principal, rec.candidat_id, resource="recommandation", resource_id=recommendation_id)
    return recommendation_service.build_recommendation_response(rec)


@router.patch(
    "/{recommendation_id}",
    response_model=RecommandationResponse,
    summary="Ajuster ou valider une recommandation (Enseignant / Admin)",
    description="L'enseignant ou l'administrateur valide ou ajuste la recommandation académique."
)
def adjust_recommendation(
    recommendation_id: int,
    data: RecommandationUpdate,
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)
    assert_can_access_candidat(db, principal, rec.candidat_id, resource="recommandation", resource_id=recommendation_id)

    if data.nom is not None:
        rec.nom = data.nom
    if data.justification is not None:
        rec.justification = data.justification
    if data.scoreComptabilite is not None:
        rec.scoreComptabilite = data.scoreComptabilite
    if data.statut is not None:
        rec.statut = data.statut

    db.commit()
    db.refresh(rec)
    return recommendation_service.build_recommendation_response(rec)


@router.post(
    "/{recommendation_id}/accept",
    summary="Accepter une recommandation (Candidat)",
    description="Le candidat accepte l'orientation recommandée."
)
def accept_recommendation(
    recommendation_id: int,
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)
    assert_can_access_candidat(db, principal, rec.candidat_id, resource="recommandation", resource_id=recommendation_id)

    rec.statut = "validée"
    db.commit()
    return {"message": "Recommandation acceptée avec succès", "statut": "validée"}


@router.post(
    "/{recommendation_id}/reject",
    summary="Refuser une recommandation (Candidat)",
    description="Le candidat rejette une recommandation pour déclencher un nouvel ajustement."
)
def reject_recommendation(
    recommendation_id: int,
    data: RecommandationUpdate,
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise ResourceNotFoundException("recommandation", recommendation_id)
    assert_can_access_candidat(db, principal, rec.candidat_id, resource="recommandation", resource_id=recommendation_id)

    rec.statut = "ajustée"
    if data.justification:
        rec.justification = data.justification
    db.commit()
    return {"message": "Recommandation rejetée. Un nouvel ajustement d'orientation est planifié.", "statut": "ajustée"}
