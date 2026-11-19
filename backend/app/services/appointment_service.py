from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import ResourceNotFoundException
from app.models.appointment import Appointment, Entretien
from app.models.candidate import CandidateProfile
from app.models.user import User


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
        Saisie du résultat d'entretien.
        Crée un Entretien associé au RendezVous avec l'avis et les notes.
        Selon le diagramme : Entretien est lié au RendezVous via rendezvous_id uniquement.
        """
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise ResourceNotFoundException("rendez-vous", appointment_id)

        # Crée ou met à jour l'Entretien associé
        entretien = apt.entretien
        if not entretien:
            entretien = Entretien(
                rendezvous_id=apt.id,
                avisEnseignant="Favorable" if decision_finale.lower() == "admis" else "Défavorable",
                notes=observations,
                staut="Terminé"
            )
            db.add(entretien)
        else:
            entretien.avisEnseignant = "Favorable" if decision_finale.lower() == "admis" else "Défavorable"
            entretien.notes = observations
            entretien.staut = "Terminé"

        # Met à jour le statut du RendezVous
        apt.statut = "confirmé"
        db.commit()
        db.refresh(apt)
        return apt


appointment_service = AppointmentService()
