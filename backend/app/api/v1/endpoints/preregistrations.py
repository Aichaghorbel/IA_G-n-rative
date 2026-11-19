"""
Endpoints API pour les Préinscriptions.
Strictement conformes au diagramme de classes UML.

Preinscription: candidat_id, formation_id, dateCreation, statut
"""
from datetime import date
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_principal, get_db, require_roles
from app.core.exceptions import (
    MissingRGPDConsentException,
    ResourceNotFoundException
)
from app.models.candidate import Candidat
from app.models.qcm import Preinscription
from app.schemas.preregistration import (
    DecisionRequest,
    PreRegistrationCreate,
    PreRegistrationResponse,
    PreRegistrationUpdate
)

router = APIRouter()


@router.post(
    "",
    response_model=PreRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une préinscription (RGPD obligatoire)",
    description="Crée une préinscription liant un Candidat à une Formation. Consentement RGPD obligatoire."
)
def create_preregistration(
    data: PreRegistrationCreate,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    # Vérification RGPD stricte
    if not data.consent_rgpd:
        raise MissingRGPDConsentException()

    # Trouve le candidat associé au compte connecté
    candidat = db.query(Candidat).filter(Candidat.user_id == principal.id).first()
    if not candidat:
        raise ResourceNotFoundException("candidat", principal.id)

    # Crée la Préinscription conforme au diagramme
    prereg = Preinscription(
        candidat_id=candidat.id,
        formation_id=data.formation_id,
        dateCreation=date.today(),
        statut="accepté"
    )
    db.add(prereg)
    db.commit()
    db.refresh(prereg)
    return prereg


@router.get(
    "/{prereg_id}",
    response_model=PreRegistrationResponse,
    summary="Consulter l'état de la préinscription",
    description="Consulte les informations de la préinscription."
)
def get_preregistration(
    prereg_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    prereg = db.query(Preinscription).filter(Preinscription.id == prereg_id).first()
    if not prereg:
        raise ResourceNotFoundException("préinscription", prereg_id)
    return prereg


@router.patch(
    "/{prereg_id}",
    response_model=PreRegistrationResponse,
    summary="Modifier la préinscription",
    description="Complète ou modifie les informations avant la prise de décision."
)
def update_preregistration(
    prereg_id: int,
    data: PreRegistrationUpdate,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    prereg = db.query(Preinscription).filter(Preinscription.id == prereg_id).first()
    if not prereg:
        raise ResourceNotFoundException("préinscription", prereg_id)

    if data.formation_id is not None:
        prereg.formation_id = data.formation_id
    if data.statut is not None:
        prereg.statut = data.statut

    db.commit()
    db.refresh(prereg)
    return prereg


@router.post(
    "/{prereg_id}/decision",
    response_model=PreRegistrationResponse,
    summary="Décision sur la préinscription (Enseignant ou Admin)",
    description="Confirme ou refuse la préinscription après examen du dossier."
)
def decide_preregistration(
    prereg_id: int,
    data: DecisionRequest,
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    prereg = db.query(Preinscription).filter(Preinscription.id == prereg_id).first()
    if not prereg:
        raise ResourceNotFoundException("préinscription", prereg_id)

    prereg.statut = data.statut
    if data.nouvelle_formation_id:
        prereg.formation_id = data.nouvelle_formation_id

    db.commit()
    db.refresh(prereg)
    return prereg
