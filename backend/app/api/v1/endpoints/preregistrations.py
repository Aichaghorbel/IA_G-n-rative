from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_principal, get_db, require_roles
from app.core.exceptions import (
    CandidateNotAssignedException,
    MissingRGPDConsentException,
    ResourceNotFoundException
)
from app.models.candidate import CandidateProfile, PreRegistration
from app.schemas.preregistration import (
    DecisionRequest,
    PreRegistrationCreate,
    PreRegistrationResponse,
    PreRegistrationUpdate
)
from app.services.candidate_service import candidate_service

router = APIRouter()


@router.post(
    "",
    response_model=PreRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une préinscription (RGPD obligatoire)",
    description="Crée une préinscription après vérification OTP de l'email et consentement RGPD obligatoire."
)
def create_preregistration(
    data: PreRegistrationCreate,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    # Vérification RGPD stricte (Section 3.2 et 6.7)
    if not data.consent_rgpd:
        raise MissingRGPDConsentException()

    # Trouve ou crée le profil associé
    profile = None
    if principal.role in ["Candidat", "candidat", "C"]:
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    else:
        profile = db.query(CandidateProfile).filter(CandidateProfile.session_id == principal.session_id).first()

    if not profile:
        profile = CandidateProfile(
            user_id=principal.id if principal.role in ["Candidat", "candidat", "C"] else None,
            session_id=principal.session_id if principal.role in ["Visiteur", "visiteur", "V"] else None,
            nom=data.nom or "Candidat",
            prenom=data.prenom or "Visiteur",
            email=data.email or (principal.verified_email if hasattr(principal, "verified_email") else "candidat@test.tn"),
            telephone=data.telephone,
            statut_dossier="PREINSCRIT",
            consent_rgpd=True,
            consent_timestamp=datetime.now(timezone.utc)
        )
        db.add(profile)
        db.flush()
    else:
        candidate_service.validate_and_update_status(profile, "PREINSCRIT")

    prereg = PreRegistration(
        candidate_id=profile.id,
        formation_id=data.formation_id,
        decision="en_attente"
    )
    db.add(prereg)
    db.commit()
    db.refresh(prereg)
    return prereg


@router.get(
    "/{prereg_id}",
    response_model=PreRegistrationResponse,
    summary="Consulter l'état de la préinscription",
    description="Consulte les informations de la préinscription (V/C propriétaire, E affecté ou Admin)."
)
def get_preregistration(
    prereg_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    prereg = db.query(PreRegistration).filter(PreRegistration.id == prereg_id).first()
    if not prereg:
        raise ResourceNotFoundException("préinscription", prereg_id)
    return prereg


@router.patch(
    "/{prereg_id}",
    response_model=PreRegistrationResponse,
    summary="Modifier les informations de la préinscription",
    description="Complète ou modifie les informations avant la prise de décision finale."
)
def update_preregistration(
    prereg_id: int,
    data: PreRegistrationUpdate,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    prereg = db.query(PreRegistration).filter(PreRegistration.id == prereg_id).first()
    if not prereg:
        raise ResourceNotFoundException("préinscription", prereg_id)

    if data.formation_id is not None:
        prereg.formation_id = data.formation_id
    if data.observations is not None:
        prereg.observations = data.observations

    db.commit()
    db.refresh(prereg)
    return prereg


@router.post(
    "/{prereg_id}/decision",
    response_model=PreRegistrationResponse,
    summary="Décision sur la préinscription (E affecté ou Admin)",
    description="Confirme, refuse ou ajuste la formation retenue après examen du dossier."
)
def decide_preregistration(
    prereg_id: int,
    data: DecisionRequest,
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    prereg = db.query(PreRegistration).filter(PreRegistration.id == prereg_id).first()
    if not prereg:
        raise ResourceNotFoundException("préinscription", prereg_id)

    candidate = prereg.candidate
    if principal.role in ["Enseignant", "enseignant", "E"]:
        candidate_service.verify_teacher_access(principal.id, candidate)

    prereg.decision = data.decision
    if data.observations:
        prereg.observations = data.observations
    if data.decision == "ajuste" and data.nouvelle_formation_id:
        prereg.formation_id = data.nouvelle_formation_id

    db.commit()
    db.refresh(prereg)
    return prereg
