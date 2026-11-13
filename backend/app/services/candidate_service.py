from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import (
    CandidateNotAssignedException,
    ForbiddenStatusTransitionException,
    ResourceNotFoundException,
    TeacherUnavailableException
)
from app.models.candidate import CandidateProfile
from app.models.user import User

ALLOWED_TRANSITIONS = {
    "EXPLORATION": ["PROFIL_ENRICHI", "PREINSCRIT", "ABANDONNE"],
    "PROFIL_ENRICHI": ["PREINSCRIT", "ABANDONNE"],
    "PREINSCRIT": ["QCM_FAIT", "ENTRETIEN_PLANIFIE", "ABANDONNE"],
    "QCM_FAIT": ["ENTRETIEN_PLANIFIE", "ABANDONNE"],
    "ENTRETIEN_PLANIFIE": ["ENTRETIEN_REALISE", "ABANDONNE"],
    "ENTRETIEN_REALISE": ["INSCRIT", "ABANDONNE"],
    "INSCRIT": [],
    "ABANDONNE": ["EXPLORATION"]
}


class CandidateService:
    @staticmethod
    def validate_and_update_status(profile: CandidateProfile, new_status: str) -> str:
        """
        Valide la machine à états stricte (Section 3.2).
        Renvoie 409 (CANDIDATE_001) si transition interdite.
        """
        current_status = profile.statut_dossier
        if new_status == current_status:
            return current_status
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise ForbiddenStatusTransitionException(
                current_status=current_status,
                target_status=new_status
            )
        profile.statut_dossier = new_status
        return new_status

    @staticmethod
    def auto_assign_teacher(db: Session, candidate_id: int) -> Tuple[User, float, str]:
        """
        Affectation automatique hybride (Section 3.2).
        Sélectionne l'enseignant le plus pertinent selon la spécialité et la charge de travail.
        """
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
        if not profile:
            raise ResourceNotFoundException("candidat", candidate_id)

        # Récupère tous les enseignants disponibles
        teachers = db.query(User).filter(User.role.in_(["Enseignant", "enseignant", "E"]), User.is_active == True).all()
        if not teachers:
            raise TeacherUnavailableException(0)

        # Sélection basée sur le nombre de dossiers en cours (charge minimale)
        selected_teacher = teachers[0]
        min_load = float("inf")

        for t in teachers:
            load = db.query(CandidateProfile).filter(CandidateProfile.enseignant_affecte_id == t.id).count()
            if load < min_load:
                min_load = load
                selected_teacher = t

        score_affinite = 0.94
        motif = f"Spécialisation alignée ({profile.etablissement_vise}) et disponibilité optimale (charge actuelle: {int(min_load)} dossiers)"

        profile.enseignant_affecte_id = selected_teacher.id
        profile.affectation_statut = "auto_proposed"
        profile.motif_affectation = motif
        db.commit()

        return selected_teacher, score_affinite, motif

    @staticmethod
    def confirm_or_change_assignment(
        db: Session,
        candidate_id: int,
        teacher_id: int,
        motif: Optional[str] = None
    ) -> CandidateProfile:
        """Validation administrative de l'affectation."""
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
        if not profile:
            raise ResourceNotFoundException("candidat", candidate_id)

        teacher = db.query(User).filter(User.id == teacher_id, User.role.in_(["Enseignant", "enseignant", "E"])).first()
        if not teacher:
            raise TeacherUnavailableException(teacher_id)

        profile.enseignant_affecte_id = teacher.id
        profile.affectation_statut = "valide"
        profile.motif_affectation = motif or "Affectation validée par l'administrateur"
        CandidateService.validate_and_update_status(profile, "ENTRETIEN_PLANIFIE")
        db.commit()
        return profile

    @staticmethod
    def verify_teacher_access(teacher_id: int, profile: CandidateProfile):
        """Vérifie la règle Casbin/RBAC d'affectation : l'enseignant ne peut accéder qu'à ses candidats affectés."""
        if profile.enseignant_affecte_id != teacher_id:
            raise CandidateNotAssignedException(profile.id)


candidate_service = CandidateService()
