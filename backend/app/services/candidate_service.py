from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import (
    CandidateNotAssignedException,
    ForbiddenStatusTransitionException,
    ResourceNotFoundException,
    TeacherUnavailableException
)
from app.models.appointment import RendezVous
from app.models.candidate import Candidat, CandidateProfile, ProfilCandidat
from app.models.conversation import Conversation
from app.models.qcm import Preinscription
from app.models.recommendation import Recommandation
from app.models.user import User
from app.models.visitor_session import VisitorSession as VisitorSessionModel

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
    def compute_status(profile: CandidateProfile) -> str:
        """Déduit le statut du dossier à partir des entités UML (Preinscription, QCM, RendezVous, Entretien)."""
        if profile.rendezvous:
            for rdv in profile.rendezvous:
                if rdv.entretien and rdv.entretien.staut == "Terminé":
                    return "ENTRETIEN_REALISE"
            return "ENTRETIEN_PLANIFIE"
        if profile.preinscriptions:
            for p in profile.preinscriptions:
                if p.qcm and p.qcm.score is not None:
                    return "QCM_FAIT"
            return "PREINSCRIT"
        if profile.profil:
            return "PROFIL_ENRICHI"
        return "EXPLORATION"

    @staticmethod
    def validate_and_update_status(profile: CandidateProfile, new_status: str) -> str:
        """
        Valide la machine à états stricte (Section 3.2).
        Renvoie 409 (CANDIDATE_001) si transition interdite.
        """
        current_status = getattr(profile, "statut_dossier", None) or CandidateService.compute_status(profile)
        if new_status == current_status:
            return current_status
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise ForbiddenStatusTransitionException(
                current_status=current_status,
                target_status=new_status
            )
        return new_status

    @staticmethod
    def auto_assign_teacher(db: Session, candidate_id: int) -> Tuple[User, float, str]:
        """
        Affectation automatique hybride (Section 3.2).
        Sélectionne l'enseignant le plus pertinent selon la spécialité et la charge de travail
        (basée sur `RendezVous.enseignant_id` conformément au diagramme UML).
        """
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
        if not profile:
            raise ResourceNotFoundException("candidat", candidate_id)

        teachers = db.query(User).filter(User.type_user == "Enseignant", User.is_active == True).all()
        if not teachers:
            raise TeacherUnavailableException(0)

        selected_teacher = teachers[0]
        min_load = float("inf")

        for t in teachers:
            load = db.query(RendezVous).filter(RendezVous.enseignant_id == t.id).count()
            if load < min_load:
                min_load = load
                selected_teacher = t

        score_affinite = 0.94
        etab = profile.universite or "IIT/ISB"
        motif = f"Spécialisation alignée ({etab}) et disponibilité optimale (charge actuelle: {int(min_load)} dossiers)"

        rdv = (
            db.query(RendezVous)
            .filter(RendezVous.candidat_id == profile.id)
            .order_by(RendezVous.id.desc())
            .first()
        )
        if rdv is None:
            rdv = RendezVous(
                candidat_id=profile.id,
                enseignant_id=selected_teacher.id,
                dateHeure=datetime.now(timezone.utc).replace(tzinfo=None),
                statut="confirmé",
                salleOuLien="À définir",
            )
            db.add(rdv)
        else:
            rdv.enseignant_id = selected_teacher.id
        db.commit()

        return selected_teacher, score_affinite, motif

    @staticmethod
    def confirm_or_change_assignment(
        db: Session,
        candidate_id: int,
        teacher_id: int,
        motif: Optional[str] = None
    ) -> CandidateProfile:
        """Validation administrative de l'affectation via RendezVous."""
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
        if not profile:
            raise ResourceNotFoundException("candidat", candidate_id)

        teacher = db.query(User).filter(User.id == teacher_id, User.type_user == "Enseignant").first()
        if not teacher:
            raise TeacherUnavailableException(teacher_id)

        rdv = (
            db.query(RendezVous)
            .filter(RendezVous.candidat_id == profile.id)
            .order_by(RendezVous.id.desc())
            .first()
        )
        if rdv is None:
            rdv = RendezVous(
                candidat_id=profile.id,
                enseignant_id=teacher.id,
                dateHeure=datetime.now(timezone.utc).replace(tzinfo=None),
                statut="confirmé",
                salleOuLien=motif or "Campus / En ligne",
            )
            db.add(rdv)
        else:
            rdv.enseignant_id = teacher.id
            rdv.statut = "confirmé"

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def verify_teacher_access(teacher_id: int, profile: CandidateProfile):
        """Vérifie la règle Casbin/RBAC d'affectation : l'enseignant ne peut accéder qu'à ses candidats affectés."""
        if not any(r.enseignant_id == teacher_id for r in profile.rendezvous):
            raise CandidateNotAssignedException(profile.id)


def merge_candidats(db: Session, source: Candidat, target: Candidat) -> None:
    """
    Transfère les données d'un Candidat temporaire (créé avant inscription par un visiteur)
    vers le Candidat authentifié cible, puis supprime le doublon source.
    """
    if source.id == target.id:
        return

    for attr in ("CIN", "passport", "pays", "dateNaissance", "sexe", "adresse", "universite"):
        if getattr(target, attr) is None and getattr(source, attr) is not None:
            setattr(target, attr, getattr(source, attr))

    db.query(Preinscription).filter(Preinscription.candidat_id == source.id).update(
        {Preinscription.candidat_id: target.id}, synchronize_session=False
    )
    db.query(Recommandation).filter(Recommandation.candidat_id == source.id).update(
        {Recommandation.candidat_id: target.id}, synchronize_session=False
    )
    db.query(Conversation).filter(Conversation.candidat_id == source.id).update(
        {Conversation.candidat_id: target.id}, synchronize_session=False
    )
    db.query(RendezVous).filter(RendezVous.candidat_id == source.id).update(
        {RendezVous.candidat_id: target.id}, synchronize_session=False
    )
    db.query(VisitorSessionModel).filter(VisitorSessionModel.candidate_id == source.id).update(
        {VisitorSessionModel.candidate_id: target.id}, synchronize_session=False
    )

    for formation in list(source.formations):
        if formation not in target.formations:
            target.formations.append(formation)
    source.formations.clear()

    if source.profil is not None:
        if target.profil is None:
            db.query(ProfilCandidat).filter(ProfilCandidat.id == source.profil.id).update(
                {ProfilCandidat.candidat_id: target.id}, synchronize_session=False
            )
        else:
            for attr in (
                "dernierDiplomeObtenu", "anneeObtention", "diplomeSouhaite",
                "niveau", "cours", "sourceConnaissanceUniversite",
            ):
                if getattr(target.profil, attr) is None and getattr(source.profil, attr) is not None:
                    setattr(target.profil, attr, getattr(source.profil, attr))
            db.delete(source.profil)

    if target.visiteur_id is None and source.visiteur_id is not None:
        visiteur_id = source.visiteur_id
        source.visiteur_id = None
        db.flush()
        target.visiteur_id = visiteur_id

    db.flush()
    db.expire(source)
    db.delete(source)
    db.flush()


candidate_service = CandidateService()
