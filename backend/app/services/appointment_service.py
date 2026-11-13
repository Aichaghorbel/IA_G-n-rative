from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import ResourceNotFoundException
from app.models.appointment import Appointment
from app.models.candidate import CandidateProfile
from app.models.user import User
from app.services.auth_service import auth_service
from app.services.candidate_service import candidate_service


class AppointmentService:
    @staticmethod
    def record_outcome(
        db: Session,
        appointment_id: int,
        decision_finale: str,
        observations: str,
        current_teacher: User
    ) -> Appointment:
        """
        Saisie du résultat et observations d'entretien (Section 3.7 & 6.8).
        Déclenche la conversion automatique visiteur -> candidat si decision_finale == 'admis'.
        """
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise ResourceNotFoundException("rendez-vous", appointment_id)

        # Vérification d'affectation
        candidate = db.query(CandidateProfile).filter(CandidateProfile.id == apt.candidat_id).first()
        if not candidate:
            raise ResourceNotFoundException("candidat", apt.candidat_id)

        if current_teacher.role in ["Enseignant", "enseignant", "E"]:
            candidate_service.verify_teacher_access(current_teacher.id, candidate)

        apt.observations = observations
        apt.decision_finale = decision_finale
        apt.status = "termine"

        # Mise à jour du statut du dossier
        candidate.statut_dossier = "ENTRETIEN_REALISE"

        # Conversion automatique du compte si admis (Section 6.8)
        if decision_finale.lower() == "admis" and candidate.session_id:
            auth_service.convert_visitor_to_candidate(
                db=db,
                session_id=candidate.session_id,
                email=candidate.email,
                nom=candidate.nom,
                prenom=candidate.prenom,
                telephone=candidate.telephone
            )

        db.commit()
        db.refresh(apt)
        return apt


appointment_service = AppointmentService()
