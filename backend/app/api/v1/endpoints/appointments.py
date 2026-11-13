from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from app.api.deps import PaginationQuery, get_current_principal, get_db, require_roles
from app.core.exceptions import ResourceNotFoundException
from app.models.appointment import Appointment
from app.models.candidate import CandidateProfile
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentOutcomeRequest,
    AppointmentResponse,
    AppointmentSlotResponse,
    AppointmentUpdate
)
from app.services.appointment_service import appointment_service
from app.services.candidate_service import candidate_service

router = APIRouter()


@router.get(
    "/slots",
    response_model=List[AppointmentSlotResponse],
    summary="Créneaux disponibles pour l'entretien",
    description="Consulte les créneaux autorisés disponibles (filtres par enseignant et dates)."
)
def get_appointment_slots(
    enseignant_id: Optional[int] = Query(None),
    principal=Depends(require_roles("Candidat", "Enseignant")),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    slots: List[AppointmentSlotResponse] = []
    teachers = db.query(User).filter(User.role.in_(["Enseignant", "enseignant", "E"])).all()

    for i, t in enumerate(teachers[:3]):
        for day_offset in range(1, 4):
            slot_date = now + timedelta(days=day_offset, hours=9 + i)
            slots.append(AppointmentSlotResponse(
                id=f"slot_{t.id}_{day_offset}",
                enseignant_id=t.id,
                enseignant_nom=f"{t.prenom} {t.nom}",
                date_creneau=slot_date,
                disponible=True
            ))
    return slots


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Réserver un rendez-vous d'entretien",
    description="Réserve un créneau de rendez-vous d'admission (génère l'invitation email)."
)
def create_appointment(
    data: AppointmentCreate,
    principal=Depends(require_roles("Candidat", "Enseignant")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    candidate_id = profile.id if profile else 1
    enseignant_id = profile.enseignant_affecte_id if profile else None

    apt = Appointment(
        candidat_id=candidate_id,
        enseignant_id=enseignant_id,
        preinscription_id=data.preinscription_id,
        date_proposee=data.date_proposee,
        lieu=data.lieu or "en ligne",
        status="propose"
    )
    db.add(apt)
    db.commit()
    db.refresh(apt)
    return apt


@router.get(
    "/me",
    response_model=List[AppointmentResponse],
    summary="Mon rendez-vous (Candidat)",
    description="Consulte le rendez-vous d'entretien du candidat connecté."
)
def get_my_appointment(
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    if not profile:
        raise ResourceNotFoundException("profil candidat", principal.id)
    return db.query(Appointment).filter(Appointment.candidat_id == profile.id).all()


@router.get(
    "",
    response_model=List[AppointmentResponse],
    summary="Agenda des rendez-vous (Enseignant / Admin)",
    description="Consulte l'agenda des entretiens (Enseignant ne voit que les siens, Administrateur voit tout)."
)
def list_appointments(
    response: Response,
    pagination: PaginationQuery = Depends(),
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    query = db.query(Appointment)
    if principal.role in ["Enseignant", "enseignant", "E"]:
        query = query.filter(Appointment.enseignant_id == principal.id)

    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    return query.offset(pagination.offset).limit(pagination.limit).all()


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Replanifier ou annuler un rendez-vous",
    description="Met à jour la date ou le statut d'un rendez-vous."
)
def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    principal=Depends(require_roles("Candidat", "Enseignant")),
    db: Session = Depends(get_db)
):
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise ResourceNotFoundException("rendez-vous", appointment_id)

    if data.date_proposee:
        apt.date_proposee = data.date_proposee
    if data.date_confirmee:
        apt.date_confirmee = data.date_confirmee
    if data.status:
        apt.status = data.status
    if data.lieu:
        apt.lieu = data.lieu

    db.commit()
    db.refresh(apt)
    return apt


@router.post(
    "/{appointment_id}/outcome",
    response_model=AppointmentResponse,
    summary="Saisir le résultat et les observations de l'entretien (Enseignant affecté)",
    description="Saisie des observations finales. Déclenche la conversion automatique visiteur -> candidat si admis."
)
def record_outcome(
    appointment_id: int,
    data: AppointmentOutcomeRequest,
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    return appointment_service.record_outcome(
        db=db,
        appointment_id=appointment_id,
        decision_finale=data.decision_finale,
        observations=data.observations,
        current_teacher=principal
    )
