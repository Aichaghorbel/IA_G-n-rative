"""
Endpoints API pour les Préinscriptions.
Strictement conformes au diagramme de classes UML.

Preinscription: candidat_id, formation_id, dateCreation, statut
"""
from datetime import date
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session
from app.api.deps import VisitorSession, get_db, require_roles
from app.api.ownership import assert_can_access_candidat, get_candidat_of, get_visiteur_for
from app.core.config import settings
from app.core.exceptions import (
    InsufficientRoleException,
    MissingRGPDConsentException,
    ResourceNotFoundException,
)
from app.core.rbac import Role
from app.models.candidate import Candidat
from app.models.formation import Formation
from app.models.qcm import Preinscription
from app.schemas.preregistration import (
    DecisionRequest,
    PreRegistrationCreate,
    PreRegistrationResponse,
    PreRegistrationUpdate,
)
from app.services.session_service import session_service

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
    request: Request,
    response: Response,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    # Vérification RGPD stricte
    if not data.consent_rgpd:
        raise MissingRGPDConsentException()

    formation = db.query(Formation).filter(Formation.id == data.formation_id).first()
    if not formation:
        raise ResourceNotFoundException("formation", data.formation_id)

    role = Role.normalize(principal.role)
    if role == Role.VISITEUR:
        if isinstance(principal, VisitorSession) and principal.is_ephemeral:
            ip = request.client.host if request.client else None
            session, token = session_service.create_session(db, ip)
            response.headers["X-Session-Token"] = token
            response.set_cookie(
                "session_token", token,
                max_age=settings.VISITOR_SESSION_EXPIRE_DAYS * 86400,
                httponly=True, samesite=settings.COOKIE_SAMESITE, secure=settings.COOKIE_SECURE,
            )
            principal = VisitorSession(session_id=str(session.id))
        visiteur = get_visiteur_for(db, principal, create=True)
        candidat = db.query(Candidat).filter(Candidat.visiteur_id == visiteur.id).first()
        if not candidat:
            candidat = Candidat(visiteur_id=visiteur.id)
            db.add(candidat)
            db.flush()
    else:
        candidat = get_candidat_of(db, principal)
        if not candidat:
            candidat = Candidat(user_id=principal.id)
            db.add(candidat)
            db.flush()

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
    assert_can_access_candidat(db, principal, prereg.candidat_id, resource="préinscription", resource_id=prereg_id)
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
    assert_can_access_candidat(db, principal, prereg.candidat_id, resource="préinscription", resource_id=prereg_id)

    if data.statut is not None:
        # La décision (accepté / refusé) appartient au personnel : voir POST /{id}/decision
        raise InsufficientRoleException("Le statut d'une préinscription ne peut être modifié que par le personnel")
    if data.formation_id is not None:
        formation = db.query(Formation).filter(Formation.id == data.formation_id).first()
        if not formation:
            raise ResourceNotFoundException("formation", data.formation_id)
        prereg.formation_id = data.formation_id

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
    assert_can_access_candidat(db, principal, prereg.candidat_id, resource="préinscription", resource_id=prereg_id)

    prereg.statut = data.statut
    if data.nouvelle_formation_id:
        prereg.formation_id = data.nouvelle_formation_id

    db.commit()
    db.refresh(prereg)
    return prereg
